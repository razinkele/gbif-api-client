"""
Marine & Biodiversity Data Explorer - Shiny Web Application

Refactored version with modular architecture:
- Constants extracted to app_modules/constants.py
- Utilities extracted to app_modules/utils.py
- UI and server logic remain in this file (can be further modularized in Phase 4)

This application provides interactive access to marine biodiversity data from GBIF,
SHARK, and other marine databases.
"""

import logging

import pandas as pd
import plotly.express as px
import threading
from shiny import App, reactive, render, ui
from shinyswatch import theme

from gbif_client import GBIFClient
from shark_client import SHARKClient
from apis.trait_ontology_db import get_trait_db

# Import from refactored modules
from app_modules.constants import (
    COUNTRY_CODES,
    SAMPLING_PROTOCOL_KEYWORDS,
    DEFAULT_OCCURRENCE_LIMIT,
    BULK_ANALYSIS_SAMPLE_SIZE,
    MAX_SIZE_MEASUREMENTS_DISPLAY,
)
from app_modules.utils import detect_size_data, validate_upload_file
from app_modules.ui.components import (
    create_species_search_panel,
    create_bulk_analysis_panel,
    create_trait_search_panel,
    create_trait_info_panel,
)
from app_modules.trait_utils import (
    get_traits_for_aphia_id,
    create_trait_summary_text,
    enrich_occurrences_with_traits,
    query_species_by_trait_range,
    get_trait_statistics,
)
from app_modules.exceptions import (
    DataValidationError,
    InvalidFileFormatError,
    InvalidFileContentError,
    FileTooLargeError,
    DatabaseError,
    DatabaseQueryError,
    TraitError,
    TraitQueryError,
)
from apis.exceptions import (
    APIError,
    APIConnectionError,
    APIRequestError,
    APIResponseError,
    APITimeoutError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app_ui = ui.div(
    ui.head_content(ui.tags.link(rel="stylesheet", href="custom.css")),
    ui.div(
            ui.h1("Marine & Biodiversity Data Explorer", class_="dashboard-header"),
            ui.layout_sidebar(
            ui.sidebar(
                create_species_search_panel(COUNTRY_CODES),
                create_trait_search_panel(),
                create_bulk_analysis_panel(),
                ui.div(ui.output_ui("progress_display"), class_="progress-card"),
                width=300,
            ),
            ui.div(
                ui.div(
                    ui.navset_tab(
                        ui.nav_panel(
                            "� Dashboard",
                            ui.div(
                                ui.h4("Bulk Analysis Dashboard"),
                                ui.output_text("bulk_analysis_summary"),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "�📋 Species",
                            ui.div(
                                ui.output_data_frame("species_table"),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "📍 Occurrences",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        8, ui.output_data_frame("occurrences_table")
                                    ),
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("📊 Statistics"),
                                            ui.output_text("stats_text"),
                                            class_="stat-card",
                                        ),
                                    ),
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🗺️ Map",
                            ui.div(ui.output_ui("map_plot"), class_="dashboard-card"),
                        ),
                        ui.nav_panel(
                            "📈 Bulk Analysis",
                            ui.div(
                                ui.output_ui("bulk_analysis_table"),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🦈 SHARK Marine Data",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Data Search"),
                                            ui.input_select(
                                                "shark_dataset",
                                                "Dataset",
                                                choices={"": "Loading..."},
                                            ),
                                            ui.input_select(
                                                "shark_parameter",
                                                "Parameter",
                                                choices={"": "Loading..."},
                                            ),
                                            ui.input_select(
                                                "shark_station",
                                                "Station",
                                                choices={"": "Loading..."},
                                            ),
                                            ui.input_date_range(
                                                "shark_date_range",
                                                "Date Range",
                                                start="2020-01-01",
                                                end="2024-12-31",
                                            ),
                                            ui.input_action_button(
                                                "shark_search_btn",
                                                "🔍 Search SHARK Data",
                                                class_="btn btn-info",
                                            ),
                                            ui.hr(),
                                            ui.h5("🌱 Freshwater Ecology (FWE)"),
                                            ui.input_text(
                                                "fwe_genus",
                                                "Genus",
                                                placeholder="e.g., Salmo",
                                            ),
                                            ui.input_text(
                                                "fwe_taxonname",
                                                "Taxon name",
                                                placeholder="e.g., Salmo salar",
                                            ),
                                            ui.input_select(
                                                "fwe_organismgroup",
                                                "Organism group",
                                                choices={"fi": "Freshwater Invertebrates (fi)", "pl": "Plants (pl)", "al": "Algae (al)"},
                                                selected="fi",
                                            ),
                                            ui.input_action_button(
                                                "fwe_search_btn",
                                                "🔎 Search FWE",
                                                class_="btn btn-success",
                                            ),
                                            ui.br(),
                                            ui.output_text("fwe_status_text"),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_ui("shark_api_banner"),
                                            ui.output_data_frame("shark_data_table"),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 Data Summary"),
                                                ui.output_text("shark_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📈 Quality Control"),
                                                ui.output_text("shark_qc_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🌿 SLU Artdatabanken (Dyntaxa)",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Taxon Search"),
                                            ui.input_text(
                                                "dyntaxa_search",
                                                "Scientific Names",
                                                placeholder="Enter species names (comma-separated)",  # noqa: E501
                                            ),
                                            ui.input_checkbox(
                                                "dyntaxa_synonyms",
                                                "Include synonyms",
                                                value=True,
                                            ),
                                            ui.input_action_button(
                                                "dyntaxa_search_btn",
                                                "🔍 Search Dyntaxa",
                                                class_="btn btn-success",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "dyntaxa_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame(
                                                "dyntaxa_results_table"
                                            ),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 Search Summary"),
                                                ui.output_text("dyntaxa_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("🔗 Taxonomy Info"),
                                                ui.output_text("dyntaxa_taxonomy_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🌊 WoRMS",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Species Search"),
                                            ui.input_text(
                                                "worms_search",
                                                "Scientific Names",
                                                placeholder="Enter species names (comma-separated)",  # noqa: E501
                                            ),
                                            ui.input_action_button(
                                                "worms_search_btn",
                                                "🔍 Search WoRMS",
                                                class_="btn btn-primary",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "worms_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame("worms_results_table"),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 Search Summary"),
                                                ui.output_text("worms_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("🆔 AphiaID Info"),
                                                ui.output_text("worms_aphia_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🪸 AlgaeBase",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Algae Search"),
                                            ui.input_text(
                                                "algaebase_search",
                                                "Search Terms",
                                                placeholder="Enter algae names or terms",  # noqa: E501
                                            ),
                                            ui.input_select(
                                                "algaebase_type",
                                                "Search Type",
                                                choices={
                                                    "taxa": "Taxa",
                                                    "genus": "Genus",
                                                },
                                            ),
                                            ui.input_action_button(
                                                "algaebase_search_btn",
                                                "🔍 Search AlgaeBase",
                                                class_="btn btn-success",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "algaebase_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame(
                                                "algaebase_results_table"
                                            ),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 Search Summary"),
                                                ui.output_text(
                                                    "algaebase_summary_text"
                                                ),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("🌿 Taxonomy Info"),
                                                ui.output_text(
                                                    "algaebase_taxonomy_text"
                                                ),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "⚠️ IOC-UNESCO HAB",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 HAB Species"),
                                            ui.input_action_button(
                                                "hab_list_btn",
                                                "📋 Get HAB List",
                                                class_="btn btn-warning",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "hab_toxins_btn",
                                                "🧪 Get Toxins List",
                                                class_="btn btn-danger",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "hab_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame("hab_results_table"),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 HAB Summary"),
                                                ui.output_text("hab_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("⚠️ Risk Assessment"),
                                                ui.output_text("hab_risk_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🌍 OBIS",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Occurrence Search"),
                                            ui.input_text(
                                                "obis_search",
                                                "Scientific Names",
                                                placeholder="Enter species names (comma-separated)",  # noqa: E501
                                            ),
                                            ui.br(),
                                            ui.h6("📍 Coordinate Lookup"),
                                            ui.input_numeric(
                                                "obis_lat", "Latitude", value=0.0
                                            ),
                                            ui.input_numeric(
                                                "obis_lon", "Longitude", value=0.0
                                            ),
                                            ui.input_action_button(
                                                "obis_search_btn",
                                                "🔍 Search OBIS",
                                                class_="btn btn-info",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "obis_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame("obis_results_table"),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 OBIS Summary"),
                                                ui.output_text("obis_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📍 Spatial Info"),
                                                ui.output_text("obis_spatial_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "❄️ Nordic Microalgae",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("🔍 Microalgae Search"),
                                            ui.input_text(
                                                "nordic_search",
                                                "Search Parameters",
                                                placeholder="Enter search terms",
                                            ),
                                            ui.input_action_button(
                                                "nordic_search_btn",
                                                "🔍 Search Nordic DB",
                                                class_="btn btn-primary",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "nordic_harmful_btn",
                                                "⚠️ Get Harmful Species",
                                                class_="btn btn-warning",
                                            ),
                                            ui.br(),
                                            ui.input_action_button(
                                                "nordic_clear_btn",
                                                "🗑️ Clear",
                                                class_="btn btn-secondary",
                                            ),
                                            class_="sidebar-card",
                                        ),
                                    ),
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.output_data_frame(
                                                "nordic_results_table"
                                            ),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("📊 Nordic Summary"),
                                                ui.output_text("nordic_summary_text"),
                                                class_="stat-card",
                                            ),
                                        ),
                                        ui.column(
                                            6,
                                            ui.div(
                                                ui.h5("⚠️ Harmfulness"),
                                                ui.output_text(
                                                    "nordic_harmfulness_text"
                                                ),
                                                class_="stat-card",
                                            ),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                        ui.nav_panel(
                            "🔬 Trait Database",
                            ui.div(
                                ui.row(
                                    ui.column(
                                        8,
                                        ui.div(
                                            ui.h5("🔍 Trait Search Results"),
                                            ui.output_data_frame("trait_search_results_table"),
                                            class_="dashboard-card",
                                        ),
                                    ),
                                    ui.column(
                                        4,
                                        ui.div(
                                            ui.h5("📊 Database Statistics"),
                                            ui.output_text("trait_db_stats"),
                                            class_="stat-card",
                                        ),
                                    ),
                                ),
                                ui.div(
                                    ui.row(
                                        ui.column(
                                            12,
                                            create_trait_info_panel(),
                                        ),
                                    )
                                ),
                                class_="dashboard-card",
                            ),
                        ),
                    ),
                    selected="Dashboard",
                    id="main_tabs",
                    class_="dashboard-main",
                )
            ),
        )
    )
)

# Apply a shinyswatch Bootswatch theme for a cleaner look
app_ui = ui.page_fluid(app_ui, theme=theme.flatly())
def server(input, output, session):  # noqa: C901
    client = GBIFClient()
    shark_client = SHARKClient(
        use_mock=True
    )  # Enable mock data for testing/offline use
    trait_db = get_trait_db()

    # Reactive values for progress tracking and results
    progress_state = reactive.Value(
        {
            "is_running": False,
            "current_species": "",
            "completed": 0,
            "total": 0,
            "status": "Ready to start analysis",
        }
    )
    current_task = reactive.Value(None)

    analysis_results = reactive.Value(pd.DataFrame())
    shark_api_message = reactive.Value("")  # Message shown in SHARK UI when API fails or fallback used

    # Cancellation event for bulk tasks (thread-safe flag)
    cancel_event = threading.Event()

    @reactive.calc
    def species_results():
        if input.search_btn() > 0 and input.species_query():
            try:
                return client.search_species(input.species_query())
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"API connection error searching for species '{input.species_query()}': {e}")
                return []
            except APIResponseError as e:
                logger.error(f"API response error searching for species '{input.species_query()}': {e}")
                return []
            except APIError as e:
                logger.error(f"API error searching for species '{input.species_query()}': {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error searching for species '{input.species_query()}': {e}")
                return []
        return []

    @reactive.calc
    def selected_species():
        results = species_results()
        if results:
            return results[0]["key"] if results else None
        return None

    @reactive.calc
    def occurrences_results():
        species_key = selected_species()
        if species_key:
            try:
                occ = client.search_occurrences(
                    taxon_key=species_key,
                    country=input.country() or None,
                    limit=DEFAULT_OCCURRENCE_LIMIT,
                )
                results = occ.get("results", [])

                if input.size_filter():
                    # Use the helper function to filter records with size data
                    filtered_results = []
                    for record in results:
                        has_size, _ = detect_size_data(record)
                        if has_size:
                            filtered_results.append(record)
                    return filtered_results
                else:
                    return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"API connection error fetching occurrences for species {species_key}: {e}")
                return []
            except APIResponseError as e:
                logger.error(f"API response error fetching occurrences for species {species_key}: {e}")
                return []
            except APIError as e:
                logger.error(f"API error fetching occurrences for species {species_key}: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching occurrences for species {species_key}: {e}")
                return []
        return []

    @output
    @render.data_frame
    def species_table():
        results = species_results()
        if results:
            df = pd.DataFrame(results)
            return df[["key", "scientificName", "rank", "status"]]
        return pd.DataFrame()

    @output
    @render.data_frame
    def occurrences_table():
        occ = occurrences_results()
        if occ:
            df = pd.DataFrame(occ)
            cols = [
                "gbifID",
                "scientificName",
                "countryCode",
                "decimalLatitude",
                "decimalLongitude",
                "eventDate",
                "individualCount",
                "organismQuantity",
                "organismQuantityType",
                "sex",
                "lifeStage",
                "reproductiveCondition",
                "behavior",
                "establishmentMeans",
                "occurrenceStatus",
                "preparations",
                "disposition",
                "occurrenceRemarks",
                "organismRemarks",
                "dynamicProperties",
            ]
            available_cols = [col for col in cols if col in df.columns]
            return df[available_cols]
        return pd.DataFrame()

    @output
    @render.ui
    def map_plot():
        occ = occurrences_results()
        if occ:
            df = pd.DataFrame(occ)
            if "decimalLatitude" in df.columns and "decimalLongitude" in df.columns:
                df = df.dropna(subset=["decimalLatitude", "decimalLongitude"])
                fig = px.scatter_mapbox(
                    df,
                    lat="decimalLatitude",
                    lon="decimalLongitude",
                    hover_name="scientificName",
                    zoom=3,
                )
                fig.update_layout(mapbox_style="open-street-map")
                return ui.HTML(fig.to_html())
        return ui.HTML("<p>No occurrence data to display on map.</p>")

    @output
    @render.text
    def stats_text():
        species_key = selected_species()
        if species_key:
            total_count = client.get_occurrence_count(
                taxon_key=species_key, country=input.country() or None
            )
            filtered_count = len(occurrences_results())
            if input.size_filter():
                sources = (
                    "📏 Size Data Sources:\n"
                    "• MeasurementOrFact extension (cell size, biovolume, etc.)\n"
                    "• Dynamic properties (morphological data)\n"
                    "• Sampling protocols (size fractions, mesh sizes)\n"
                    "• Known datasets: KPLANK, San Francisco Bay Phytoplankton,\n"
                    "  Tara Oceans"
                )
                return (
                    f"Total occurrences: {total_count} | "
                    f"Filtered with size data: {filtered_count}\n\n"
                    + sources
                )
            else:
                return f"Total occurrences: {total_count}"
        return "Select a species to see stats"

    @output
    @render.ui
    def bulk_analysis_table():
        df = analysis_results.get()
        if df.empty:
            return ui.HTML("<p>No partial results yet. Run an analysis to see progress here.</p>")

        # Get current species from progress state to highlight it
        state = progress_state.get()
        current = state.get("current_species", "")
        is_running = state.get("is_running", False)

        # Build HTML table with simple row highlighting
        headers = list(df.columns)
        html = [
            '<div style="max-height:400px; overflow:auto;">',
            # Legend for colors
            '<div style="font-size:0.85em; margin-bottom:8px;">'
            '<span style="background:#e9f7ef;padding:4px;border-radius:3px;margin-right:8px;">&nbsp;&nbsp;</span> Processed'
            '<span style="margin-left:16px; background:#fff3cd;padding:4px;border-radius:3px;margin-right:8px;">&nbsp;&nbsp;</span> Processing'
            '</div>',
            '<table class="table table-sm" style="width:100%; border-collapse:collapse;">',
            '<thead style="position:sticky; top:0; background:#f8f9fa; z-index:1;"><tr>'
        ]
        for h in headers:
            html.append(f"<th style='border-bottom:1px solid #ddd; padding:6px; text-align:left;'>{h}</th>")
        html.append("</tr></thead><tbody>")

        for _, row in df.iterrows():
            species = str(row.get("Species Name", ""))
            # Default processed style
            row_style = "background:#e9f7ef;"  # light green for completed
            text_style = ""
            # Highlight the current species if running
            if is_running and species and current and species == current:
                row_style = "background:#fff3cd;"  # light yellow for processing
                text_style = "font-weight:700;"

            html.append("<tr style='" + row_style + "'>")
            for h in headers:
                cell = row.get(h, "")
                # Escape HTML in cell content
                cell_text = str(cell)
                html.append(
                    f"<td style='padding:6px; border-bottom:1px solid #eee; {text_style}'>{cell_text}</td>"
                )
            html.append("</tr>")

        html.append("</tbody></table></div>")
        return ui.HTML("".join(html))

    @reactive.calc
    def progress_state_calc():
        state = progress_state.get()
        logger.debug(f"Progress state updated: {state}")
        return state

    @reactive.calc
    def progress_html():
        state = progress_state_calc()
        task = current_task.get()

        if state["total"] == 0:
            return """<h5>⚡ Analysis Progress</h5>
            <p style="font-size: 0.9em; margin: 5px 0;">Ready to analyze species</p>"""

        # Consider task running if the reactive state indicates analysis is in progress
        # or the underlying task reports a running status.
        task_running = state.get("is_running", False) or (task is not None and task.status() == "running")

        # Create compact progress HTML for sidebar
        progress_html = f"""
        <h5>⚡ Analysis Progress</h5>
        <div style="margin: 10px 0;">
            <div style="font-size: 0.9em; margin-bottom: 5px;">
                <span>{state['total']} species</span>
            </div>
        """

        if task_running:
            progress_html += """
            <div style="width: 100%;
                        background-color: #f0f0f0;
                        border-radius: 5px;
                        height: 12px;
                        overflow: hidden;">
                <div style="width: 100%; height: 12px;
                            background: linear-gradient(
                                90deg,
                                #4CAF50 25%,
                                transparent 25%,
                                transparent 50%,
                                #4CAF50 50%,
                                #4CAF50 75%,
                                transparent 75%,
                                transparent
                            );
                            background-size: 40px 40px;
                            animation: progress-animation 1s linear infinite;"></div>
            </div>
            <style>
                @keyframes progress-animation {
                    0% { background-position: 0 0; }
                    100% { background-position: 40px 0; }
                }
            </style>
            <div style="font-size: 0.85em; color: #ff9800; margin-top: 8px;">
                ⏳ Analyzing... (check console for progress)
            </div>

            <div style="font-size: 0.85em; color: #333; margin-top: 6px;">
                <strong>Status:</strong> {state.get('status', '')}
            </div>
            <div style="font-size: 0.85em; color: #333; margin-top: 4px;">
                <strong>Progress:</strong> {state.get('completed', 0)} / {state.get('total', 0)} completed
            </div>
            """
        elif int(state.get("completed", 0)) > 0:
            progress_html += """
            <div style="width: 100%;
                        background-color: #4CAF50;
                        border-radius: 5px;
                        height: 12px;"></div>
            <div style="color: #4CAF50;
                        font-size: 0.9em;
                        margin-top: 8px;">
                ✓ Completed! Check Bulk Analysis tab.
            </div>
            """
        else:
            progress_html += """
            <div style="width: 100%;
                        background-color: #f0f0f0;
                        border-radius: 5px;
                        height: 12px;"></div>
            <div style="font-size: 0.85em;
                        color: #666;
                        margin-top: 8px;">
                Waiting to start...
            </div>
            """

        progress_html += "</div>"
        return progress_html

    @output
    @render.ui
    def progress_display():
        html = progress_html()
        return ui.HTML(html)

    @reactive.calc
    def bulk_analysis_trigger():
        # This will trigger when analyze_btn is clicked and there's a file
        btn_click = input.analyze_btn()
        file_info = input.species_file()
        if btn_click > 0 and file_info is not None:
            logger.info(f"Bulk analysis triggered - button clicks: {btn_click}")
            return True
        return False

    @reactive.calc
    def bulk_analysis_first_trigger():
        # This will trigger when analyze_first_btn is clicked and there's a file
        btn_click = input.analyze_first_btn()
        file_info = input.species_file()
        if btn_click > 0 and file_info is not None:
            logger.info(f"Bulk analysis first species triggered - button clicks: {btn_click}")
            return True
        return False

    @reactive.calc
    def uploaded_file_df():
        """Read the uploaded Excel file with no header so we can inspect columns and header row."""
        file_info = input.species_file()
        if not file_info:
            return pd.DataFrame()
        try:
            file_content = file_info[0]["datapath"]
            df_raw = pd.read_excel(file_content, sheet_name=0, header=None)
            return df_raw
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logger.error(f"Excel file parsing error: {e}")
            return pd.DataFrame()
        except (OSError, IOError) as e:
            logger.error(f"File system error reading uploaded file: {e}")
            return pd.DataFrame()
        except ValueError as e:
            logger.error(f"Invalid Excel file format: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error reading uploaded file: {e}")
            return pd.DataFrame()

    @reactive.effect
    def update_species_column_choices():
        """Update the species_column select choices after a file is uploaded or header flag changes."""
        df_raw = uploaded_file_df()
        # If no file, keep default choice
        if df_raw.empty:
            try:
                ui.update_select("species_column", choices={"0": "Column 1"}, selected="0")
            except (AttributeError, KeyError) as e:
                logger.debug(f"UI component error updating species_column: {e}")
            except Exception as e:
                logger.debug(f"Unexpected error updating species_column (no file): {e}")
            return

        try:
            choices = {}
            header_row = df_raw.iloc[0] if df_raw.shape[0] > 0 else None
            for i in range(df_raw.shape[1]):
                label = f"Column {i+1}"
                if input.species_has_header() and header_row is not None:
                    try:
                        name = str(header_row[i])
                        if name and name.lower() not in ("nan", "none"):
                            label = f"Column {i+1} - {name}"
                    except (ValueError, TypeError, AttributeError):
                        # Can't convert header value to string, use default label
                        pass
                choices[str(i)] = label

            # Default to previously selected if still present, otherwise first
            selected = input.species_column() if input.species_column() in choices else next(iter(choices))
            ui.update_select("species_column", choices=choices, selected=selected)
        except (IndexError, KeyError) as e:
            logger.error(f"Data access error updating species column choices: {e}")
        except (AttributeError, TypeError) as e:
            logger.error(f"UI component error updating species column choices: {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating species column choices: {e}")

    def _get_species_samples_from_file(df_raw, col_idx, has_header, sample_size=3):
        """Extract species samples from uploaded file for preview."""
        if has_header:
            series = df_raw.iloc[1:, col_idx]
        else:
            series = df_raw.iloc[:, col_idx]
        return series.dropna().astype(str).str.strip().head(sample_size).tolist()

    def _query_database_preview(db_name, species_name, client, shark_client):
        """Query a single database and return True if match found."""
        try:
            if db_name == "gbif":
                res = client.search_species(species_name, limit=1)
                return bool(res)
            elif db_name == "shark":
                worms = shark_client.get_worms_taxa(scientific_name=str(species_name), limit=1)
                return isinstance(worms, pd.DataFrame) and not worms.empty
            elif db_name == "fwe":
                fwe = shark_client.search_fwe_taxa(str(species_name), limit=1)
                return isinstance(fwe, pd.DataFrame) and not fwe.empty
            elif db_name == "obis":
                obis = shark_client.get_obis_records([str(species_name)])
                return isinstance(obis, pd.DataFrame) and not obis.empty
            elif db_name == "algaebase":
                al = shark_client.match_algaebase_taxa([str(species_name)])
                return isinstance(al, pd.DataFrame) and not al.empty
        except (APIConnectionError, APITimeoutError):
            # Network error - treat as no match
            pass
        except (APIResponseError, APIError):
            # API error - treat as no match
            pass
        except (ValueError, TypeError, AttributeError):
            # Data conversion error - treat as no match
            pass
        return False

    @reactive.calc
    def preview_counts():
        """Produce small sample match counts and average latency for each supported DB."""
        import time

        databases = ["gbif", "shark", "fwe", "obis", "algaebase"]

        # Early return conditions
        if not input.enable_previews():
            return {db: "Disabled" for db in databases}

        df_raw = uploaded_file_df()
        if df_raw.empty:
            return {db: "No file" for db in databases}

        # Validate column selection
        try:
            col_idx = int(input.species_column() or 0)
        except (ValueError, TypeError):
            # Invalid column index, use default
            col_idx = 0

        if col_idx < 0 or col_idx >= df_raw.shape[1]:
            return {db: "Col out of range" for db in databases}

        # Extract species samples
        species_samples = _get_species_samples_from_file(
            df_raw, col_idx, input.species_has_header(), sample_size=3
        )

        if not species_samples:
            return {db: "No names" for db in databases}

        # Initialize counters
        counts = {db: 0 for db in databases}
        times = {db: 0.0 for db in databases}
        calls = {db: 0 for db in databases}

        # Query each database for each species
        for name in species_samples:
            for db in databases:
                start = time.perf_counter()
                calls[db] += 1
                if _query_database_preview(db, name, client, shark_client):
                    counts[db] += 1
                times[db] += time.perf_counter() - start

        # Format results
        total = len(species_samples)
        result = {}
        for db in databases:
            if calls[db] > 0:
                avg = times[db] / calls[db]
                result[db] = f"{counts[db]}/{total} ({avg:.2f}s)"
            else:
                result[db] = f"{counts[db]}/{total} (n/a)"

        return result

    @output
    @render.text
    def preview_gbif():
        p = preview_counts()
        return p.get("gbif", "N/A")

    @output
    @render.text
    def preview_shark():
        p = preview_counts()
        return p.get("shark", "N/A")

    @output
    @render.text
    def preview_fwe():
        p = preview_counts()
        return p.get("fwe", "N/A")

    @output
    @render.text
    def preview_obis():
        p = preview_counts()
        return p.get("obis", "N/A")

    @output
    @render.text
    def preview_algaebase():
        p = preview_counts()
        return p.get("algaebase", "N/A")

    def _process_gbif_data(species_name, species_data, client):
        """Process GBIF data for a species."""
        if not species_data:
            return {
                "GBIF Match": "Not found",
                "Taxon Key": "",
                "Total Occurrences": "0",
                "Has Size Data": "No",
                "Size Measurements": "N/A",
            }

        taxon_key = species_data[0].get("key")
        occ = client.search_occurrences(taxon_key=taxon_key, limit=BULK_ANALYSIS_SAMPLE_SIZE)
        occurrences = occ.get("results", [])

        # Detect size data
        has_size_data = False
        size_measurements = []
        for record in occurrences:
            has_size, measurements = detect_size_data(record)
            if has_size:
                has_size_data = True
                size_measurements.extend(measurements)
                break

        return {
            "GBIF Match": species_data[0].get("scientificName"),
            "Taxon Key": taxon_key,
            "Total Occurrences": occ.get("count", 0),
            "Has Size Data": "Yes" if has_size_data else "No",
            "Size Measurements": "; ".join(size_measurements[:MAX_SIZE_MEASUREMENTS_DISPLAY]) if size_measurements else "None found",
        }

    def _process_fwe_data(species_name, shark_client):
        """Process Freshwater Ecology data for a species."""
        try:
            fwe_df = shark_client.search_fwe_taxa(str(species_name), limit=1)
            if not fwe_df.empty:
                fwe_id = fwe_df.iloc[0].get("id") if "id" in fwe_df.columns else None
                fwe_name = fwe_df.iloc[0].get("scientificName") if "scientificName" in fwe_df.columns else None
                result = {
                    "FWE Match": fwe_name or "Found",
                    "FWE Taxon ID": str(fwe_id) if fwe_id is not None else ""
                }
                if fwe_id is not None:
                    occ_df = shark_client.get_fwe_occurrences(fwe_id, limit=BULK_ANALYSIS_SAMPLE_SIZE)
                    result["FWE Occurrences"] = str(len(occ_df) if isinstance(occ_df, pd.DataFrame) else 0)
                else:
                    result["FWE Occurrences"] = "Unknown"
                return result
            return {"FWE Match": "Not found", "FWE Occurrences": "0"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.debug(f"FWE API connection error for {species_name}: {e}")
            return {"FWE Match": f"Connection Error"}
        except (APIResponseError, APIError) as e:
            logger.debug(f"FWE API response error for {species_name}: {e}")
            return {"FWE Match": f"API Error"}
        except Exception as e:
            logger.debug(f"Unexpected error in FWE lookup for {species_name}: {e}")
            return {"FWE Match": f"Error: {str(e)}"}

    def _process_worms_data(species_name, shark_client):
        """Process WoRMS taxonomy data for a species."""
        try:
            worms_df = shark_client.get_worms_taxa(scientific_name=str(species_name), limit=1)
            if not worms_df.empty:
                worms_name = worms_df.iloc[0].get("scientificname") if "scientificname" in worms_df.columns else None
                worms_id = worms_df.iloc[0].get("AphiaID") if "AphiaID" in worms_df.columns else None
                return {
                    "WoRMS Match": worms_name or "Found",
                    "WoRMS AphiaID": str(worms_id) if worms_id is not None else ""
                }
            return {"WoRMS Match": "Not found"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.debug(f"WoRMS API connection error for {species_name}: {e}")
            return {"WoRMS Match": f"Connection Error"}
        except (APIResponseError, APIError) as e:
            logger.debug(f"WoRMS API response error for {species_name}: {e}")
            return {"WoRMS Match": f"API Error"}
        except Exception as e:
            logger.debug(f"Unexpected error in WoRMS lookup for {species_name}: {e}")
            return {"WoRMS Match": f"Error: {str(e)}"}

    def _process_obis_data(species_name, shark_client):
        """Process OBIS occurrence data for a species."""
        try:
            obis_df = shark_client.get_obis_records([str(species_name)])
            return {"OBIS Occurrences": str(len(obis_df) if isinstance(obis_df, pd.DataFrame) else 0)}
        except (APIConnectionError, APITimeoutError) as e:
            logger.debug(f"OBIS API connection error for {species_name}: {e}")
            return {"OBIS Occurrences": f"Connection Error"}
        except (APIResponseError, APIError) as e:
            logger.debug(f"OBIS API response error for {species_name}: {e}")
            return {"OBIS Occurrences": f"API Error"}
        except Exception as e:
            logger.debug(f"Unexpected error in OBIS lookup for {species_name}: {e}")
            return {"OBIS Occurrences": f"Error: {str(e)}"}

    def _process_algaebase_data(species_name, shark_client):
        """Process AlgaeBase taxonomy data for a species."""
        try:
            al_df = shark_client.match_algaebase_taxa([str(species_name)])
            if not al_df.empty:
                name = al_df.iloc[0].get("name") if "name" in al_df.columns else None
                return {"AlgaeBase Match": str(name) if name is not None else "Found"}
            return {"AlgaeBase Match": "Not found"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.debug(f"AlgaeBase API connection error for {species_name}: {e}")
            return {"AlgaeBase Match": f"Connection Error"}
        except (APIResponseError, APIError) as e:
            logger.debug(f"AlgaeBase API response error for {species_name}: {e}")
            return {"AlgaeBase Match": f"API Error"}
        except Exception as e:
            logger.debug(f"Unexpected error in AlgaeBase lookup for {species_name}: {e}")
            return {"AlgaeBase Match": f"Error: {str(e)}"}

    def _update_progress(species_name, completed, total, results):
        """Update reactive progress state and results."""
        try:
            progress_state.set({
                "is_running": True,
                "current_species": str(species_name),
                "completed": completed,
                "total": total,
                "status": f"Processing {completed}/{total}: {species_name}",
            })
            analysis_results.set(pd.DataFrame(results))
        except Exception:
            logger.debug("Could not update reactive progress", exc_info=True)

    # Extended task for bulk analysis
    @reactive.extended_task
    async def bulk_analysis_task(species_list, dbs: dict | None = None):
        """
        Process species list in background task.
        Cannot access reactive values - all updates happen via return value.
        """
        import asyncio

        try:
            logger.info(f"=== TASK STARTED: Processing {len(species_list)} species ===")
            results = []
            local_cache = {}  # Local cache just for this task

            for i, species_name in enumerate(species_list):
                # Check for cancellation request before processing each species
                if cancel_event.is_set():
                    logger.info("Cancellation requested: stopping bulk analysis early")
                    # Update progress_state to reflect cancellation and return partial results
                    try:
                        progress_state.set(
                            {
                                "is_running": False,
                                "current_species": "",
                                "completed": i,
                                "total": len(species_list),
                                "status": f"Cancelled after processing {i}/{len(species_list)} species",
                            }
                        )
                        analysis_results.set(pd.DataFrame(results))
                    except Exception:
                        logger.debug("Could not update reactive state after cancellation", exc_info=True)

                    # Update UI to show Cancelled state for the button
                    try:
                        ui.update_action_button("cancel_btn", label="Cancelled", disabled=True)
                    except Exception:
                        logger.debug("Could not update cancel button to 'Cancelled'", exc_info=True)

                    return results

                logger.info(
                    f"Processing species {i+1}/{len(species_list)}: {species_name}"
                )

                # Yield control periodically
                if i % 5 == 0:
                    await asyncio.sleep(0)

                try:
                    # Check cache first to avoid repeated API calls
                    species_key = str(species_name).strip().lower()
                    if species_key in local_cache:
                        species_data = local_cache[species_key]
                        logger.debug(f"Using cached data for {species_name}")
                    else:
                        species_data = client.search_species(str(species_name), limit=1)
                        local_cache[species_key] = species_data

                    # Initialize result with species name
                    result = {"Species Name": str(species_name)}

                    # Process GBIF data
                    gbif_selected = True if dbs is None else bool(dbs.get("gbif", True))
                    if gbif_selected:
                        result.update(_process_gbif_data(species_name, species_data, client))
                    else:
                        result.update({
                            "GBIF Match": "Skipped",
                            "Taxon Key": "",
                            "Total Occurrences": "0",
                            "Has Size Data": "No",
                            "Size Measurements": "N/A",
                        })

                    # Process other databases if requested
                    if dbs is not None:
                        if dbs.get("fwe"):
                            result.update(_process_fwe_data(species_name, shark_client))
                        if dbs.get("shark"):
                            result.update(_process_worms_data(species_name, shark_client))
                        if dbs.get("obis"):
                            result.update(_process_obis_data(species_name, shark_client))
                        if dbs.get("algaebase"):
                            result.update(_process_algaebase_data(species_name, shark_client))

                    # Append result and update progress
                    results.append(result)
                    logger.info("Completed processing %s", species_name)
                    _update_progress(species_name, i + 1, len(species_list), results)

                except (APIConnectionError, APITimeoutError) as e:
                    logger.error(f"API connection error processing {species_name}: {e}")
                    results.append({
                        "Species Name": str(species_name),
                        "GBIF Match": "Connection Error",
                        "Taxon Key": None,
                        "Total Occurrences": 0,
                        "Has Size Data": "No",
                        "Size Measurements": "Connection error",
                    })
                    _update_progress(species_name, i + 1, len(species_list), results)
                except (APIResponseError, APIError) as e:
                    logger.error(f"API error processing {species_name}: {e}")
                    results.append({
                        "Species Name": str(species_name),
                        "GBIF Match": "API Error",
                        "Taxon Key": None,
                        "Total Occurrences": 0,
                        "Has Size Data": "No",
                        "Size Measurements": "API error",
                    })
                    _update_progress(species_name, i + 1, len(species_list), results)
                except Exception as e:
                    logger.error(f"Unexpected error processing {species_name}: {e}", exc_info=True)
                    results.append({
                        "Species Name": str(species_name),
                        "GBIF Match": f"Error: {str(e)}",
                        "Taxon Key": None,
                        "Total Occurrences": 0,
                        "Has Size Data": "No",
                        "Size Measurements": "Error during processing",
                    })
                    _update_progress(species_name, i + 1, len(species_list), results)

            logger.info(f"=== TASK COMPLETED: Processed {len(results)} species ===")
            return results
        except Exception as task_error:
            logger.error(
                f"FATAL ERROR in bulk_analysis_task: {task_error}", exc_info=True
            )
            raise

    @reactive.effect
    def run_bulk_analysis():
        if not bulk_analysis_trigger():
            return

        # Switch to Bulk Analysis tab to see results
        ui.update_navs("main_tabs", selected="📈 Bulk Analysis")

        logger.info("Starting bulk analysis...")

        file_info = input.species_file()
        if not file_info:
            logger.warning("No file provided for bulk analysis")
            return

        # Validate the uploaded file
        is_valid, error_message = validate_upload_file(file_info, max_size_mb=10)
        if not is_valid:
            logger.error(f"File validation failed: {error_message}")
            progress.set_message(f"❌ Error: {error_message}")
            return

        # Read the Excel file
        file_content = file_info[0]["datapath"]
        logger.info(f"Processing file: {file_content}")

        try:
            # Read the Excel file

            df = pd.read_excel(file_content, sheet_name=0, header=None)

            # Validate file structure
            if df.empty:
                raise ValueError("Excel file is empty")

            if df.shape[1] < 1:
                raise ValueError("Excel file must have at least one column")

            # Determine selected column index (default to 0 if not specified)
            try:
                col_idx = int(input.species_column() or 0)
            except (ValueError, TypeError) as e:
                # Invalid column value, use default
                logger.debug(f"Invalid column index value, using default: {e}")
                col_idx = 0
            except AttributeError as e:
                # Input component not available
                logger.debug(f"Column input not available, using default: {e}")
                col_idx = 0
            except Exception as e:
                # Unexpected error
                logger.warning(f"Unexpected error getting column index, using default: {e}")
                col_idx = 0

            if col_idx < 0 or col_idx >= df.shape[1]:
                raise ValueError("Selected species column index is out of range")

            # Extract species list based on header selection
            if input.species_has_header():
                species_series = df.iloc[1:, col_idx]
            else:
                species_series = df.iloc[:, col_idx]

            species_list = species_series.dropna().astype(str).str.strip().tolist()

            if not species_list:
                raise ValueError(
                    "No species names found; ensure the selected column contains species names."
                )

            logger.info(f"Found {len(species_list)} species in file")

            # Initialize progress
            # Compute selected DB names directly from inputs (we may not have 'dbs' yet)
            selected_db_names = []
            try:
                if input.bulk_db_gbif():
                    selected_db_names.append("GBIF")
                if input.bulk_db_shark():
                    selected_db_names.append("SHARK")
                if input.bulk_db_fwe():
                    selected_db_names.append("FWE")
                if input.bulk_db_obis():
                    selected_db_names.append("OBIS")
                if input.bulk_db_algaebase():
                    selected_db_names.append("AlgaeBase")
            except (AttributeError, KeyError) as e:
                # If input component isn't available, default to GBIF
                logger.debug(f"Input components not available for DB selection: {e}")
                selected_db_names = ["GBIF"]
            except Exception as e:
                # Unexpected error accessing inputs
                logger.warning(f"Unexpected error accessing DB selection inputs: {e}")
                selected_db_names = ["GBIF"]

            selected_names = ", ".join(selected_db_names) if selected_db_names else "GBIF"

            progress_state.set(
                {
                    "is_running": True,
                    "current_species": "",
                    "completed": 0,
                    "total": len(species_list),
                    "status": f"Starting analysis of {len(species_list)} species - DBs: {selected_names}",
                }
            )

            # Start the extended task
            logger.info(
                f"About to invoke bulk_analysis_task with {len(species_list)} species"
            )
            # Clear any previous cancel request before starting
            try:
                cancel_event.clear()
            except (AttributeError, RuntimeError) as e:
                # If cancel_event is not available or already cleared
                logger.debug(f"Could not clear cancel event prior to task start: {e}")
            except Exception as e:
                # Unexpected error with threading event
                logger.warning(f"Unexpected error clearing cancel event: {e}", exc_info=True)

            # Reset cancel button to default and enable it when we start a new run
            try:
                ui.update_action_button("cancel_btn", label="✖️ Cancel", disabled=False)
            except (AttributeError, KeyError, TypeError) as e:
                # UI component not available or invalid parameters
                logger.debug(f"Could not reset cancel button when starting task: {e}")
            except Exception as e:
                # Unexpected UI error
                logger.warning(f"Unexpected error resetting cancel button: {e}", exc_info=True)

            # Determine selected databases for this run and pass to task
            dbs = {
                "gbif": bool(input.bulk_db_gbif()),
                "shark": bool(input.bulk_db_shark()),
                "fwe": bool(input.bulk_db_fwe()),
                "obis": bool(input.bulk_db_obis()),
                "algaebase": bool(input.bulk_db_algaebase()),
            }
            logger.info(f"Databases selected for bulk analysis: {', '.join([k for k, v in dbs.items() if v])}")

            task = bulk_analysis_task(species_list, dbs)
            current_task.set(task)
            logger.info("Task invocation completed")

        except ValueError as e:
            logger.error(f"File validation error: {e}")
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": 0,
                    "total": 0,
                    "status": f"Validation Error: {str(e)}",
                }
            )
            analysis_results.set(
                pd.DataFrame({"Error": [f"File validation failed: {str(e)}"]})
            )
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logger.error(f"File parsing error in bulk analysis: {e}")
            progress_state.set(
                {"is_running": False, "current_species": "", "completed": 0, "total": 0, "status": "File parsing error"}
            )
            analysis_results.set(pd.DataFrame({"Error": ["File parsing error"]}))
        except (OSError, IOError) as e:
            logger.error(f"File system error in bulk analysis: {e}")
            progress_state.set(
                {"is_running": False, "current_species": "", "completed": 0, "total": 0, "status": "File access error"}
            )
            analysis_results.set(pd.DataFrame({"Error": ["File access error"]}))
        except Exception as e:
            logger.error(f"Unexpected error processing file: {e}", exc_info=True)
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": 0,
                    "total": 0,
                    "status": f"Error: {str(e)}",
                }
            )
            analysis_results.set(
                pd.DataFrame({"Error": [f"Failed to process file: {str(e)}"]})
            )

    @reactive.effect
    def run_bulk_analysis_first():
        if not bulk_analysis_first_trigger():
            return

        # Switch to Bulk Analysis tab to see results
        ui.update_navs("main_tabs", selected="📈 Bulk Analysis")

        logger.info("Starting bulk analysis for first species...")

        file_info = input.species_file()
        if not file_info:
            logger.warning("No file provided for bulk analysis")
            return

        # Validate the uploaded file
        is_valid, error_message = validate_upload_file(file_info, max_size_mb=10)
        if not is_valid:
            logger.error(f"File validation failed: {error_message}")
            progress.set_message(f"❌ Error: {error_message}")
            return

        # Read the Excel file
        file_content = file_info[0]["datapath"]
        logger.info(f"Processing file: {file_content}")

        try:
            # Read the Excel file

            df = pd.read_excel(file_content, sheet_name=0, header=None)

            # Validate file structure
            if df.empty:
                raise ValueError("Excel file is empty")

            if df.shape[1] < 1:
                raise ValueError("Excel file must have at least one column")

            # Determine selected column index (default to 0 if not specified)
            try:
                col_idx = int(input.species_column() or 0)
            except (ValueError, TypeError) as e:
                # Invalid column value, use default
                logger.debug(f"Invalid column index value, using default: {e}")
                col_idx = 0
            except AttributeError as e:
                # Input component not available
                logger.debug(f"Column input not available, using default: {e}")
                col_idx = 0
            except Exception as e:
                # Unexpected error
                logger.warning(f"Unexpected error getting column index, using default: {e}")
                col_idx = 0

            if col_idx < 0 or col_idx >= df.shape[1]:
                raise ValueError("Selected species column index is out of range")

            # Extract species names from the selected column
            if input.species_has_header():
                series = df.iloc[1:, col_idx]  # Skip header row
            else:
                series = df.iloc[:, col_idx]

            # Clean and filter species names
            species_list = (
                series.dropna()
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)  # Normalize whitespace
                .tolist()
            )

            if not species_list:
                raise ValueError("No valid species names found in selected column")

            # Take only the first species
            first_species = species_list[0]
            logger.info(f"Analyzing first species: {first_species}")

            # Initialize progress state
            progress_state.set(
                {
                    "is_running": True,
                    "current_species": "",
                    "completed": 0,
                    "total": 1,
                    "status": f"Starting analysis of first species: {first_species}",
                }
            )

            # Clear any previous results
            analysis_results.set(pd.DataFrame())

            # Clear any previous cancel request before starting
            try:
                cancel_event.clear()
            except (AttributeError, RuntimeError) as e:
                # If cancel_event is not available or already cleared
                logger.debug(f"Could not clear cancel event prior to first species task start: {e}")
            except Exception as e:
                # Unexpected error with threading event
                logger.warning(f"Unexpected error clearing cancel event for first species: {e}", exc_info=True)

            # Reset cancel button to default and enable it when we start a new run
            try:
                ui.update_action_button("cancel_btn", label="✖️ Cancel", disabled=False)
            except (AttributeError, KeyError, TypeError) as e:
                # UI component not available or invalid parameters
                logger.debug(f"Could not reset cancel button when starting first species task: {e}")
            except Exception as e:
                # Unexpected UI error
                logger.warning(f"Unexpected error resetting cancel button for first species: {e}", exc_info=True)

            # Determine selected databases for this run and pass to task
            dbs = {
                "gbif": bool(input.bulk_db_gbif()),
                "shark": bool(input.bulk_db_shark()),
                "fwe": bool(input.bulk_db_fwe()),
                "obis": bool(input.bulk_db_obis()),
                "algaebase": bool(input.bulk_db_algaebase()),
            }
            logger.info(f"Databases selected for first species analysis: {', '.join([k for k, v in dbs.items() if v])}")

            task = bulk_analysis_task([first_species], dbs)
            current_task.set(task)
            logger.info("First species task invocation completed")

        except ValueError as e:
            logger.error(f"File validation error: {e}")
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": 0,
                    "total": 0,
                    "status": f"Validation Error: {str(e)}",
                }
            )
            analysis_results.set(
                pd.DataFrame({"Error": [f"File validation failed: {str(e)}"]})
            )
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logger.error(f"File parsing error for first species: {e}")
            progress_state.set(
                {"is_running": False, "current_species": "", "completed": 0, "total": 0, "status": "File parsing error"}
            )
            analysis_results.set(pd.DataFrame({"Error": ["File parsing error"]}))
        except (OSError, IOError) as e:
            logger.error(f"File system error for first species: {e}")
            progress_state.set(
                {"is_running": False, "current_species": "", "completed": 0, "total": 0, "status": "File access error"}
            )
            analysis_results.set(pd.DataFrame({"Error": ["File access error"]}))
        except Exception as e:
            logger.error(f"Unexpected error processing file for first species: {e}", exc_info=True)
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": 0,
                    "total": 0,
                    "status": f"Error: {str(e)}",
                }
            )
            analysis_results.set(
                pd.DataFrame({"Error": [f"Failed to process file: {str(e)}"]})
            )

    @reactive.effect
    def handle_bulk_analysis_result():
        task = current_task.get()
        if task is None:
            logger.debug("Task is None")
            return

        status = task.status()
        logger.info(f"Task status: {status}")

        if status == "completed":
            logger.info("Task completed successfully, processing results")
            results = task.result()
            analysis_results.set(pd.DataFrame(results))
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": len(results),
                    "total": len(results),
                    "status": f"Analysis completed! Processed {len(results)} species.",
                }
            )

            # Reset cancel button to default and enable it
            try:
                ui.update_action_button("cancel_btn", label="✖️ Cancel", disabled=False)
            except Exception:
                logger.debug("Could not reset cancel button state after completion", exc_info=True)
        elif status == "error":
            error = task.error()
            logger.error(f"Task failed with error: {error}")
            progress_state.set(
                {
                    "is_running": False,
                    "current_species": "",
                    "completed": 0,
                    "total": 0,
                    "status": f"Error: {str(error)}",
                }
            )
            analysis_results.set(
                pd.DataFrame({"Error": [f"Analysis failed: {str(error)}"]})
            )

            # Reset cancel button in case it was disabled
            try:
                ui.update_action_button("cancel_btn", label="✖️ Cancel", disabled=False)
            except (AttributeError, KeyError, TypeError) as e:
                # UI component not available or invalid parameters
                logger.debug(f"Could not reset cancel button state after error: {e}")
            except Exception as e:
                # Unexpected UI error
                logger.warning(f"Unexpected error resetting cancel button after task error: {e}", exc_info=True)
        elif status == "running":
            logger.debug("Task is still running")

    @reactive.effect
    @reactive.event(input.cancel_btn)
    def cancel_analysis():
        # Request cancellation via cancel_event; if the running task honors this it will stop early
        logger.warning("Cancel requested - setting cancel flag and updating UI")
        try:
            cancel_event.set()
        except Exception:
            logger.debug("Could not set cancel event", exc_info=True)

        # Update UI immediately to indicate cancellation requested
        progress_state.set(
            {
                "is_running": False,
                "current_species": "",
                "completed": 0,
                "total": 0,
                "status": "Cancel requested - stopping soon",
            }
        )

        # Update button label to indicate cancellation and disable it
        try:
            ui.update_action_button("cancel_btn", label="Cancelling…", disabled=True)
        except Exception:
            logger.debug("Could not update cancel button state", exc_info=True)

        # Keep any interim results visible for the user
        # Do not clear analysis_results here so partial results remain visible
        logger.info("Cancellation flag set; UI updated")

    @reactive.effect
    @reactive.event(input.clear_btn)
    def clear():
        ui.update_text("species_query", value="")
        ui.update_select("country", selected="")
        # Reset progress state
        progress_state.set(
            {
                "is_running": False,
                "current_species": "",
                "completed": 0,
                "total": 0,
                "status": "Ready to start analysis",
            }
        )
        analysis_results.set(pd.DataFrame())
        logger.info("UI cleared and state reset")

    # Update SHARK dropdowns
    @reactive.effect
    def update_shark_dropdowns():
        ui.update_select("shark_dataset", choices=shark_datasets())
        ui.update_select("shark_parameter", choices=shark_parameters())
        ui.update_select("shark_station", choices=shark_stations())

    # SHARK dropdown data
    @reactive.calc
    def shark_datasets():
        try:
            datasets = shark_client.get_datasets()
            # Surface fallback/error messages to UI
            if getattr(datasets, "attrs", {}).get("api_fallback"):
                shark_api_message.set("⚠️ SHARK API unreachable: using fallback dataset list (offline mode).")
            elif getattr(datasets, "attrs", {}).get("api_error"):
                shark_api_message.set(f"⚠️ SHARK API error: {datasets.attrs.get('api_error')}")
            else:
                shark_api_message.set("")
            if not datasets.empty:
                return {row["id"]: row["name"] for _, row in datasets.iterrows()}
            else:
                return {"": "No datasets available"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"SHARK API connection error fetching datasets: {e}")
            shark_api_message.set(f"⚠️ Connection error fetching datasets")
            return {"": "Error loading datasets"}
        except (APIResponseError, APIError) as e:
            logger.error(f"SHARK API response error fetching datasets: {e}")
            shark_api_message.set(f"⚠️ API error fetching datasets")
            return {"": "Error loading datasets"}
        except Exception as e:
            logger.error(f"Unexpected error fetching SHARK datasets: {e}")
            shark_api_message.set(f"⚠️ Error fetching datasets: {e}")
            return {"": "Error loading datasets"}

    @reactive.calc
    def shark_stations():
        try:
            stations = shark_client.get_stations()
            if getattr(stations, "attrs", {}).get("api_fallback"):
                shark_api_message.set("⚠️ SHARK API unreachable: using fallback station list (offline mode).")
            elif getattr(stations, "attrs", {}).get("api_error"):
                shark_api_message.set(f"⚠️ SHARK API error: {stations.attrs.get('api_error')}")
            else:
                shark_api_message.set("")
            if not stations.empty:
                return {row["id"]: row["name"] for _, row in stations.iterrows()}
            else:
                return {"": "No stations available"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"SHARK API connection error fetching stations: {e}")
            shark_api_message.set(f"⚠️ Connection error fetching stations")
            return {"": "Error loading stations"}
        except (APIResponseError, APIError) as e:
            logger.error(f"SHARK API response error fetching stations: {e}")
            shark_api_message.set(f"⚠️ API error fetching stations")
            return {"": "Error loading stations"}
        except Exception as e:
            logger.error(f"Unexpected error fetching SHARK stations: {e}")
            shark_api_message.set(f"⚠️ Error fetching stations: {e}")
            return {"": "Error loading stations"}

    @reactive.calc
    def shark_parameters():
        try:
            parameters = shark_client.get_parameters()
            if getattr(parameters, "attrs", {}).get("api_fallback"):
                shark_api_message.set("⚠️ SHARK API unreachable: using fallback parameter list (offline mode).")
            elif getattr(parameters, "attrs", {}).get("api_error"):
                shark_api_message.set(f"⚠️ SHARK API error: {parameters.attrs.get('api_error')}")
            else:
                shark_api_message.set("")
            if not parameters.empty:
                return {row["id"]: row["name"] for _, row in parameters.iterrows()}
            else:
                return {"": "No parameters available"}
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"SHARK API connection error fetching parameters: {e}")
            shark_api_message.set(f"⚠️ Connection error fetching parameters")
            return {"": "Error loading parameters"}
        except (APIResponseError, APIError) as e:
            logger.error(f"SHARK API response error fetching parameters: {e}")
            shark_api_message.set(f"⚠️ API error fetching parameters")
            return {"": "Error loading parameters"}
        except Exception as e:
            logger.error(f"Unexpected error fetching SHARK parameters: {e}")
            shark_api_message.set(f"⚠️ Error fetching parameters: {e}")
            return {"": "Error loading parameters"}

    # SHARK data reactive
    @reactive.calc
    def shark_data():
        if input.shark_search_btn() > 0:
            try:
                # Get date range
                date_range = input.shark_date_range()
                start_date = date_range[0] if date_range else None
                end_date = date_range[1] if date_range and len(date_range) > 1 else None

                # Search SHARK data
                data = shark_client.search_data(
                    parameter=input.shark_parameter() or None,
                    station=input.shark_station() or None,
                    dataset=input.shark_dataset() or None,
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000,
                )
                # Surface API status for search results
                if getattr(data, "attrs", {}).get("api_error"):
                    shark_api_message.set(f"⚠️ SHARK API error: {data.attrs.get('api_error')}")
                elif getattr(data, "attrs", {}).get("api_fallback"):
                    shark_api_message.set("⚠️ SHARK API unreachable: search returned fallback or limited/no data.")
                else:
                    # Do not clear if higher-level dropdown warnings exist
                    if not getattr(data, "attrs", {}).get("api_fallback"):
                        shark_api_message.set("")
                return data
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"SHARK API connection error searching data: {e}")
                shark_api_message.set(f"⚠️ Connection error searching SHARK data")
                return pd.DataFrame({"Error": ["Failed to search SHARK data: Connection error"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"SHARK API response error searching data: {e}")
                shark_api_message.set(f"⚠️ API error searching SHARK data")
                return pd.DataFrame({"Error": ["Failed to search SHARK data: API error"]})
            except Exception as e:
                logger.error(f"Unexpected error searching SHARK data: {e}")
                shark_api_message.set(f"⚠️ Error searching SHARK data: {e}")
                return pd.DataFrame(
                    {"Error": [f"Failed to search SHARK data: {str(e)}"]}
                )
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Freshwater Ecology (FWE) integration
    # ------------------------------------------------------------------
    @reactive.calc
    def fwe_status():
        try:
            if shark_client.fwe_api is None:
                return "FWE client not initialized"
            status = shark_client.fwe_api.get_status()
            if isinstance(status, dict):
                return f"FWE status: {status.get('status', 'unknown')}"
            return "FWE status: unavailable"
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"FWE API connection error fetching status: {e}")
            return "Error: FWE connection failed"
        except (APIResponseError, APIError) as e:
            logger.error(f"FWE API response error fetching status: {e}")
            return "Error: FWE API error"
        except Exception as e:
            logger.error(f"Unexpected error fetching FWE status: {e}")
            return f"Error fetching FWE status: {e}"

    @reactive.calc
    def fwe_search():
        if input.fwe_search_btn() > 0:
            try:
                q = input.fwe_taxonname() or input.fwe_genus() or ""
                if not q.strip():
                    return pd.DataFrame({"Message": ["Provide a genus or taxon name to search."]})

                df = shark_client.search_fwe_taxa(q, limit=100)
                # Surface api metadata in banner if present
                if getattr(df, "attrs", {}).get("api_error"):
                    shark_api_message.set(f"⚠️ FWE API error: {df.attrs.get('api_error')}")
                elif getattr(df, "attrs", {}).get("api_fallback"):
                    shark_api_message.set("⚠️ FWE API unreachable: using fallback data or limited results.")
                else:
                    # If SHARK message contains something higher priority, keep it
                    if not getattr(df, "attrs", {}).get("api_fallback"):
                        shark_api_message.set("")
                return df
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"FWE API connection error searching taxa: {e}")
                shark_api_message.set(f"⚠️ FWE connection error")
                return pd.DataFrame({"Error": ["Connection error searching FWE"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"FWE API response error searching taxa: {e}")
                shark_api_message.set(f"⚠️ FWE API error")
                return pd.DataFrame({"Error": ["API error searching FWE"]})
            except Exception as e:
                logger.error(f"Unexpected error searching FWE taxa: {e}")
                shark_api_message.set(f"⚠️ Error searching FWE: {e}")
                return pd.DataFrame({"Error": [str(e)]})
        return pd.DataFrame()

    @output
    @render.data_frame
    def shark_data_table():
        data = shark_data()
        # If FWE search produced results, display them here as well
        if not data.empty:
            return data

        # Otherwise, show default message
        msg = "No data found. Try adjusting your search criteria."
        error = getattr(data, "attrs", {}).get("api_error")
        fallback = getattr(data, "attrs", {}).get("api_fallback")
        if error:
            msg = f"⚠️ SHARK API: {error}. {msg}"
        elif fallback:
            msg = f"⚠️ SHARK API unreachable - using fallback data (may be limited). {msg}"

        # Also check if there is an FWE result (from fwe_search) requested by the user
        fwe_df = fwe_search()
        if not fwe_df.empty:
            return fwe_df

        return pd.DataFrame({"Message": [msg]})

    @output
    @render.text
    def bulk_analysis_summary():
        df = analysis_results.get()
        if df.empty:
            return "No bulk analysis results yet. Run an analysis to populate the dashboard."

        try:
            total = len(df)
            processed = df.shape[0]
            # simple coverage metrics
            gbif_matches = 0
            fwe_matches = 0
            obis_count = 0
            algaebase_matches = 0
            worms_matches = 0

            if "GBIF Match" in df.columns:
                gbif_matches = df["GBIF Match"].apply(lambda x: isinstance(x, str) and x != "Not found" and not x.startswith("Error")).sum()
            if "FWE Match" in df.columns:
                fwe_matches = df["FWE Match"].apply(lambda x: isinstance(x, str) and x != "Not found" and not x.startswith("Error")).sum()
            if "OBIS Occurrences" in df.columns:
                obis_count = df["OBIS Occurrences"].apply(lambda x: isinstance(x, int) and x > 0).sum()
            if "AlgaeBase Match" in df.columns:
                algaebase_matches = df["AlgaeBase Match"].apply(lambda x: isinstance(x, str) and x != "Not found" and not x.startswith("Error")).sum()
            if "WoRMS Match" in df.columns:
                worms_matches = df["WoRMS Match"].apply(lambda x: isinstance(x, str) and x != "Not found" and not x.startswith("Error")).sum()

            summary = (
                f"Total species processed: {total}\n"
                f"GBIF matches: {gbif_matches}\n"
                f"FWE matches: {fwe_matches}\n"
                f"WoRMS matches: {worms_matches}\n"
                f"OBIS with occurrences: {obis_count}\n"
                f"AlgaeBase matches: {algaebase_matches}\n"
            )
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating summary: {str(e)}"

    @output
    @render.text
    def shark_summary_text():
        data = shark_data()
        status_msg = shark_api_message.get() if 'shark_api_message' in globals() or True else ""
        if data.empty:
            base = "No data to summarize"
            if status_msg:
                return f"{status_msg}\n\n{base}"
            return base

        try:
            def _uniq(col):
                if col in data.columns:
                    return data.get(col, pd.Series()).nunique()
                return "N/A"

            parameters = _uniq("parameter")
            stations = _uniq("station")
            if "date" in data.columns:
                date_min = data.get("date", pd.Series()).min()
                date_max = data.get("date", pd.Series()).max()
            else:
                date_min, date_max = "N/A", "N/A"

            summary = (
                f"Total Records: {len(data)}\n"
                f"Parameters: {parameters}\n"
                f"Stations: {stations}\n"
                f"Date Range: {date_min} to {date_max}\n"
            )
            if status_msg:
                return f"{status_msg}\n\n{summary.strip()}"
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing SHARK data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing SHARK data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating SHARK summary: {str(e)}"

    @output
    @render.text
    def shark_qc_text():
        dataset = input.shark_dataset()
        if not dataset:
            return "Select a dataset to view quality control information"

        try:
            qc_info = shark_client.get_quality_control_info(dataset)
            if qc_info:
                qc_text = f"""
Quality Control Status: {qc_info.get('status', 'Unknown')}
Last Updated: {qc_info.get('last_updated', 'Unknown')}
QC Procedures: {qc_info.get('procedures', 'Not specified')}
Data Validation: {qc_info.get('validation', 'Not specified')}
"""
                return qc_text.strip()
            else:
                return "Quality control information not available for this dataset"
        except (APIConnectionError, APITimeoutError) as e:
            return f"Connection error fetching QC info: {str(e)}"
        except (APIResponseError, APIError) as e:
            return f"API error fetching QC info: {str(e)}"
        except Exception as e:
            return f"Unexpected error fetching QC info: {str(e)}"

    @output
    @render.ui
    def shark_api_banner():
        """Persistent banner shown in the SHARK panel when API errors/fallbacks occur (SHARK and FWE)."""
        try:
            msg = shark_api_message.get()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing shark_api_message: {e}")
            msg = ""
        except Exception as e:
            logger.debug(f"Unexpected error in shark_api_banner: {e}")
            msg = ""

        if not msg:
            # Return empty HTML to avoid layout jumps
            return ui.HTML("")

        # Use Bootstrap alert for consistent styling
        html = f"""
<div class="alert alert-warning" role="alert" style="border-left:4px solid #f0ad4e; background:#fff3cd; padding:10px; margin-bottom:10px;">
  <strong>API Warning:</strong> {msg}
</div>
"""
        return ui.HTML(html)

    # ============================================================================
    # Dyntaxa (SLU Artdatabanken) Functions
    # ============================================================================

    @reactive.calc
    def dyntaxa_results():
        if input.dyntaxa_search_btn() > 0 and input.dyntaxa_search():
            try:
                names = [
                    name.strip()
                    for name in input.dyntaxa_search().split(",")
                    if name.strip()
                ]
                if names:
                    results = shark_client.match_dyntaxa_taxa(names)
                    return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"Dyntaxa API connection error: {e}")
                return pd.DataFrame({"Error": ["Connection error searching Dyntaxa"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"Dyntaxa API response error: {e}")
                return pd.DataFrame({"Error": ["API error searching Dyntaxa"]})
            except Exception as e:
                logger.error(f"Unexpected error searching Dyntaxa: {e}")
                return pd.DataFrame({"Error": [f"Failed to search Dyntaxa: {str(e)}"]})
        return pd.DataFrame()

    @output
    @render.data_frame
    def dyntaxa_results_table():
        data = dyntaxa_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Enter scientific names and click Search to find matches"
                    ]
                }
            )
        return data

    @output
    @render.text
    def dyntaxa_summary_text():
        data = dyntaxa_results()
        if data.empty:
            return "No search performed"

        try:
            def _uniq(col):
                if col in data.columns:
                    return data.get(col, pd.Series()).nunique()
                return "N/A"

            scientific_count = _uniq("scientificName")
            taxon_ids_count = _uniq("taxonId")
            ranks = (
                ", ".join(data.get("rank", pd.Series()).unique()[:5])
                if "rank" in data.columns
                else "N/A"
            )

            summary = (
                f"Total Matches: {len(data)}\n"
                f"Scientific Names: {scientific_count}\n"
                f"Taxon IDs: {taxon_ids_count}\n"
                f"Ranks: {ranks}\n"
            )
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing Dyntaxa data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing Dyntaxa data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating Dyntaxa summary: {str(e)}"

    @output
    @render.text
    def dyntaxa_taxonomy_text():
        data = dyntaxa_results()
        if data.empty:
            return "No taxonomy data available"

        try:
            taxonomy_info = """
Swedish Taxonomy Database (Dyntaxa)
• Maintained by SLU Artdatabanken
• Comprehensive Swedish flora and fauna
• Includes synonyms and taxonomic hierarchy
• Used for biodiversity monitoring in Sweden
"""
            return taxonomy_info.strip()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing Dyntaxa taxonomy data: {e}")
            return "Error displaying taxonomy information"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @reactive.effect
    @reactive.event(input.dyntaxa_clear_btn)
    def clear_dyntaxa():
        ui.update_text("dyntaxa_search", value="")
        logger.info("Dyntaxa search cleared")

    # ============================================================================
    # WoRMS Functions
    # ============================================================================

    @reactive.calc
    def worms_results():
        if input.worms_search_btn() > 0 and input.worms_search():
            try:
                names = [
                    name.strip()
                    for name in input.worms_search().split(",")
                    if name.strip()
                ]
                if names:
                    results = shark_client.get_worms_records(names)
                    return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"WoRMS API connection error: {e}")
                return pd.DataFrame({"Error": ["Connection error searching WoRMS"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"WoRMS API response error: {e}")
                return pd.DataFrame({"Error": ["API error searching WoRMS"]})
            except Exception as e:
                logger.error(f"Unexpected error searching WoRMS: {e}")
                return pd.DataFrame({"Error": [f"Failed to search WoRMS: {str(e)}"]})
        return pd.DataFrame()

    @output
    @render.data_frame
    def worms_results_table():
        data = worms_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Enter scientific names and click Search to find WoRMS records."
                    ]
                }
            )
        return data

    @output
    @render.text
    def worms_summary_text():
        data = worms_results()
        if data.empty:
            return "No search performed"

        try:
            def _uniq(col):
                if col in data.columns:
                    return data.get(col, pd.Series()).nunique()
                return "N/A"

            scientific_count = _uniq("scientificname")
            aphia_count = _uniq("AphiaID")
            ranks = (
                ", ".join(data.get("rank", pd.Series()).unique()[:5])
                if "rank" in data.columns
                else "N/A"
            )

            summary = (
                f"Total Records: {len(data)}\n"
                f"Scientific Names: {scientific_count}\n"
                f"AphiaIDs: {aphia_count}\n"
                f"Taxonomic Ranks: {ranks}\n"
            )
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing WoRMS data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing WoRMS data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating WoRMS summary: {str(e)}"

    @output
    @render.text
    def worms_aphia_text():
        data = worms_results()
        if data.empty:
            return "No AphiaID data available"

        try:
            aphia_info = """
World Register of Marine Species (WoRMS)
• Global marine species database
• AphiaID: unique identifier for each taxon
• Comprehensive taxonomic classification
• Essential for marine biodiversity research
"""
            return aphia_info.strip()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing WoRMS AphiaID data: {e}")
            return "Error displaying AphiaID information"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @reactive.effect
    @reactive.event(input.worms_clear_btn)
    def clear_worms():
        ui.update_text("worms_search", value="")
        logger.info("WoRMS search cleared")

    # ============================================================================
    # AlgaeBase Functions
    # ============================================================================

    @reactive.calc
    def algaebase_results():
        if input.algaebase_search_btn() > 0 and input.algaebase_search():
            try:
                search_terms = [
                    term.strip()
                    for term in input.algaebase_search().split(",")
                    if term.strip()
                ]
                if search_terms:
                    if input.algaebase_type() == "taxa":
                        results = shark_client.match_algaebase_taxa(search_terms)
                    else:  # genus
                        results = shark_client.match_algaebase_genus(search_terms)
                    return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"AlgaeBase API connection error: {e}")
                return pd.DataFrame({"Error": ["Connection error searching AlgaeBase"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"AlgaeBase API response error: {e}")
                return pd.DataFrame({"Error": ["API error searching AlgaeBase"]})
            except Exception as e:
                logger.error(f"Unexpected error searching AlgaeBase: {e}")
                return pd.DataFrame(
                    {"Error": [f"Failed to search AlgaeBase: {str(e)}"]}
                )
        return pd.DataFrame()

    @output
    @render.data_frame
    def algaebase_results_table():
        data = algaebase_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Enter search terms and click Search to find AlgaeBase records."
                    ]
                }
            )
        return data

    @output
    @render.text
    def algaebase_summary_text():
        data = algaebase_results()
        if data.empty:
            return "No search performed"

        try:
            def _uniq(col):
                if col in data.columns:
                    return data.get(col, pd.Series()).nunique()
                return "N/A"

            classes = (
                ", ".join(data.get("class", pd.Series()).unique()[:3])
                if "class" in data.columns
                else "N/A"
            )
            genera = _uniq("genus")
            summary = (
                f"Total Records: {len(data)}\n"
                f"Search Type: {input.algaebase_type()}\n"
                f"Genera: {genera}\n"
                f"Classes: {classes}\n"
            )
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing AlgaeBase data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing AlgaeBase data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating AlgaeBase summary: {str(e)}"

    @output
    @render.text
    def algaebase_taxonomy_text():
        data = algaebase_results()
        if data.empty:
            return "No taxonomy data available"

        try:
            taxonomy_info = """
AlgaeBase Database
• Comprehensive algae taxonomy database
• Covers all groups of algae worldwide
• Includes freshwater and marine species
• Essential for phycological research
"""
            return taxonomy_info.strip()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing AlgaeBase taxonomy data: {e}")
            return "Error displaying taxonomy information"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @reactive.effect
    @reactive.event(input.algaebase_clear_btn)
    def clear_algaebase():
        ui.update_text("algaebase_search", value="")
        logger.info("AlgaeBase search cleared")

    # ============================================================================
    # IOC-UNESCO HAB Functions
    # ============================================================================

    @reactive.calc
    def hab_results():
        if input.hab_list_btn() > 0 or input.hab_toxins_btn() > 0:
            try:
                if input.hab_list_btn() > 0:
                    results = shark_client.get_hab_list()
                    results["type"] = "HAB Species"
                elif input.hab_toxins_btn() > 0:
                    results = shark_client.get_toxin_list()
                    results["type"] = "Toxins"
                else:
                    return pd.DataFrame()
                return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"HAB API connection error: {e}")
                return pd.DataFrame({"Error": ["Connection error fetching HAB data"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"HAB API response error: {e}")
                return pd.DataFrame({"Error": ["API error fetching HAB data"]})
            except Exception as e:
                logger.error(f"Unexpected error fetching HAB data: {e}")
                return pd.DataFrame({"Error": [f"Failed to fetch HAB data: {str(e)}"]})
        return pd.DataFrame()

    @output
    @render.data_frame
    def hab_results_table():
        data = hab_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Click buttons above to fetch HAB species or toxin lists."
                    ]
                }
            )
        return data

    @output
    @render.text
    def hab_summary_text():
        data = hab_results()
        if data.empty:
            return "No data fetched"

        try:
            data_type = (
                data.get("type", pd.Series()).iloc[0]
                if "type" in data.columns
                else "Unknown"
            )
            summary = f"""
Data Type: {data_type}
Total Records: {len(data)}
"""
            def _uniq(col):
                if col in data.columns:
                    return data.get(col, pd.Series()).nunique()
                return "N/A"

            if data_type == "HAB Species":
                species_count = _uniq("species")
                toxicity = (
                    ", ".join(data.get("toxicity", pd.Series()).unique()[:3])
                    if "toxicity" in data.columns
                    else "N/A"
                )
                summary += f"Species: {species_count}\n"
                summary += f"Toxicity Levels: {toxicity}"
            else:
                toxins_count = _uniq("toxin")
                types = (
                    ", ".join(data.get("type", pd.Series()).unique()[:3])
                    if "type" in data.columns
                    else "N/A"
                )
                summary += f"Toxins: {toxins_count}\n"
                summary += f"Types: {types}"

            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing HAB data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing HAB data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating HAB summary: {str(e)}"

    @output
    @render.text
    def hab_risk_text():
        data = hab_results()
        if data.empty:
            return "No risk assessment available"

        try:
            risk_info = """
IOC-UNESCO HAB & Toxins Database
• Harmful Algae: Species causing harmful algal blooms
• Toxins: Marine biotoxins affecting seafood safety
• Risk Assessment: Essential for aquaculture and fisheries
• Global monitoring and research coordination
"""
            return risk_info.strip()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing HAB risk data: {e}")
            return "Error displaying risk information"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @reactive.effect
    @reactive.event(input.hab_clear_btn)
    def clear_hab():
        logger.info("HAB data cleared")

    # ============================================================================
    # OBIS Functions
    # ============================================================================

    @reactive.calc
    def obis_results():
        if input.obis_search_btn() > 0:
            try:
                # Check if coordinate lookup or species search
                if input.obis_lat() is not None and input.obis_lon() is not None:
                    # Coordinate lookup
                    coordinates = [
                        {"latitude": input.obis_lat(), "longitude": input.obis_lon()}
                    ]
                    results = shark_client.lookup_xy(pd.DataFrame(coordinates))
                elif input.obis_search():
                    # Species search
                    names = [
                        name.strip()
                        for name in input.obis_search().split(",")
                        if name.strip()
                    ]
                    if names:
                        results = shark_client.get_obis_records(names)
                    else:
                        return pd.DataFrame()
                else:
                    return pd.DataFrame()
                return results
            except (APIConnectionError, APITimeoutError) as e:
                logger.error(f"OBIS API connection error: {e}")
                return pd.DataFrame({"Error": ["Connection error searching OBIS"]})
            except (APIResponseError, APIError) as e:
                logger.error(f"OBIS API response error: {e}")
                return pd.DataFrame({"Error": ["API error searching OBIS"]})
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid coordinates for OBIS search: {e}")
                return pd.DataFrame({"Error": ["Invalid search parameters"]})
            except Exception as e:
                logger.error(f"Unexpected error searching OBIS: {e}")
                return pd.DataFrame({"Error": [f"Failed to search OBIS: {str(e)}"]})
        return pd.DataFrame()

    @output
    @render.data_frame
    def obis_results_table():
        data = obis_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Enter search terms or coordinates and click Search"
                    ]
                }
            )
        return data

    @output
    @render.text
    def obis_summary_text():
        data = obis_results()
        if data.empty:
            return "No search performed"

        try:
            if "species" in data.columns:
                species_count = data.get("species", pd.Series()).nunique()
            else:
                species_count = "N/A"

            if "depth" in data.columns:
                depth_min = data.get("depth", pd.Series()).min()
                depth_max = data.get("depth", pd.Series()).max()
            else:
                depth_min, depth_max = "N/A", "N/A"

            summary = (
                f"Total Records: {len(data)}\n"
                f"Species: {species_count}\n"
                f"Depth Range: {depth_min} - {depth_max} m\n"
            )
            return summary.strip()
        except (KeyError, IndexError) as e:
            return f"Error accessing OBIS data for summary: {str(e)}"
        except (ValueError, TypeError) as e:
            return f"Error processing OBIS data for summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating OBIS summary: {str(e)}"

    @output
    @render.text
    def obis_spatial_text():
        data = obis_results()
        if data.empty:
            return "No spatial data available"

        try:
            spatial_info = """
Ocean Biodiversity Information System (OBIS)
• Global marine biodiversity database
• Species occurrence data worldwide
• Depth, location, and environmental data
• Essential for marine ecosystem research
"""
            return spatial_info.strip()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Error accessing OBIS spatial data: {e}")
            return "Error displaying spatial information"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @reactive.effect
    @reactive.event(input.obis_clear_btn)
    def clear_obis():
        ui.update_text("obis_search", value="")
        ui.update_numeric("obis_lat", value=None)
        ui.update_numeric("obis_lon", value=None)
        logger.info("OBIS search cleared")

    # ============================================================================
    # Nordic Microalgae Functions
    # ============================================================================

    @reactive.calc
    def nordic_results():
        if input.nordic_search_btn() > 0 and input.nordic_search():
            try:
                search_params = {"query": input.nordic_search()}
                results = shark_client.get_nordic_microalgae_taxa(search_params)
                return results
            except Exception as e:
                logger.error(f"Error searching Nordic Microalgae: {e}")
                return pd.DataFrame(
                    {"Error": [f"Failed to search Nordic DB: {str(e)}"]}
                )
        elif input.nordic_harmful_btn() > 0:
            try:
                # Get all taxa and filter harmful ones
                all_taxa = shark_client.get_nordic_microalgae_taxa()
                if not all_taxa.empty and "harmfulness" in all_taxa.columns:
                    harmful_taxa = all_taxa[
                        all_taxa["harmfulness"].str.contains(
                            "toxic", case=False, na=False
                        )
                    ]
                    return harmful_taxa
                return pd.DataFrame({"Message": ["No harmful species data available"]})
            except Exception as e:
                logger.error(f"Error fetching harmful species: {e}")
                return pd.DataFrame(
                    {"Error": [f"Failed to fetch harmful species: {str(e)}"]}
                )
        return pd.DataFrame()

    @output
    @render.data_frame
    def nordic_results_table():
        data = nordic_results()
        if data.empty:
            return pd.DataFrame(
                {
                    "Message": [
                        "Enter search terms or click Get Harmful Species"
                    ]
                }
            )
        return data

    @output
    @render.text
    def nordic_summary_text():
        data = nordic_results()
        if data.empty:
            return "No search performed"

        try:
            harmfulness = (
                ", ".join(data.get("harmfulness", pd.Series()).unique()[:3])
                if "harmfulness" in data.columns
                else "N/A"
            )

            if "name" in data.columns:
                species_count = data.get("name", pd.Series()).nunique()
            else:
                species_count = "N/A"

            summary = (
                f"Total Records: {len(data)}\n"
                f"Species: {species_count}\n"
                f"Harmfulness Levels: {harmfulness}\n"
            )
            return summary.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    @output
    @render.text
    def nordic_harmfulness_text():
        data = nordic_results()
        if data.empty:
            return "No harmfulness data available"

        try:
            harmful_info = """
Nordic Microalgae Database
• Focus on Nordic freshwater microalgae
• Harmfulness assessment for toxic species
• Essential for water quality monitoring
• Cyanobacteria and other harmful algae
"""
            return harmful_info.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    @reactive.effect
    @reactive.event(input.nordic_clear_btn)
    def clear_nordic():
        ui.update_text("nordic_search", value="")
        logger.info("Nordic Microalgae search cleared")

    # ============================================================================
    # Trait Database Functions
    # ============================================================================

    trait_search_results = reactive.Value(pd.DataFrame())

    @reactive.calc
    def trait_db_statistics():
        """Get trait database statistics."""
        try:
            return get_trait_statistics(trait_db)
        except (DatabaseQueryError, TraitQueryError) as e:
            logger.error(f"Database/trait query error getting statistics: {e}")
            return {}
        except (DatabaseError, TraitError) as e:
            logger.error(f"Database/trait error getting statistics: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting trait statistics: {e}")
            return {}

    @render.text
    def trait_db_stats():
        """Display trait database statistics."""
        stats = trait_db_statistics()
        if not stats:
            return "Trait database statistics not available"

        lines = [
            f"Total Species: {stats.get('total_species', 0):,}",
            f"Total Traits: {stats.get('total_traits', 0)}",
            f"Total Trait Values: {stats.get('total_trait_values', 0):,}",
            "",
            "Species by Source:"
        ]

        species_by_source = stats.get('species_by_source', {})
        for source, count in species_by_source.items():
            lines.append(f"  • {source}: {count:,}")

        return "\n".join(lines)

    @render.text
    def trait_search_results_count():
        """Display count of trait search results."""
        results = trait_search_results()
        if results.empty:
            return ""
        return f"Found {len(results)} species"

    @render.data_frame
    def trait_search_results_table():
        """Display trait search results."""
        results = trait_search_results()
        if results.empty:
            return pd.DataFrame({"Message": ["No results - perform a trait search"]})

        # Format the results for display
        display_df = results.copy()

        # Select and rename columns for better display
        cols_to_show = ['aphia_id', 'scientific_name', 'genus', 'trait_value']
        if 'common_name' in display_df.columns:
            cols_to_show.insert(2, 'common_name')

        display_df = display_df[cols_to_show]
        display_df.columns = ['AphiaID', 'Scientific Name', 'Genus', 'Trait Value']
        if 'common_name' in cols_to_show:
            display_df.columns = ['AphiaID', 'Scientific Name', 'Common Name', 'Genus', 'Trait Value']

        return render.DataGrid(display_df, width="100%", height="600px")

    @render.text
    def trait_info_text():
        """Display detailed trait information for selected species."""
        results = trait_search_results()
        if results.empty:
            return "Select a species from the trait search results to view detailed trait information."

        # Get the first species from results
        if len(results) > 0:
            aphia_id = results.iloc[0]['aphia_id']

            try:
                trait_info = get_traits_for_aphia_id(trait_db, aphia_id)
                if trait_info:
                    return create_trait_summary_text(trait_info)
                else:
                    return f"No trait information found for AphiaID {aphia_id}"
            except (DatabaseQueryError, TraitQueryError) as e:
                logger.error(f"Database/trait query error fetching info for AphiaID {aphia_id}: {e}")
                return f"Error fetching trait information: {str(e)}"
            except (DatabaseError, TraitError) as e:
                logger.error(f"Database/trait error fetching info for AphiaID {aphia_id}: {e}")
                return f"Error fetching trait information: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error fetching trait info for AphiaID {aphia_id}: {e}")
                return f"Error fetching trait information: {str(e)}"

        return "No species selected"

    @reactive.effect
    @reactive.event(input.trait_search_btn)
    def perform_trait_search():
        """Perform trait search when button is clicked."""
        trait_name = input.trait_name()

        if not trait_name:
            logger.warning("No trait selected for search")
            return

        logger.info(f"Performing trait search for: {trait_name}")

        try:
            if trait_name in ['biovolume', 'carbon_content']:
                # Numeric trait search
                min_val = input.trait_min_value()
                max_val = input.trait_max_value()

                results = query_species_by_trait_range(
                    trait_db,
                    trait_name=trait_name,
                    min_value=min_val,
                    max_value=max_val,
                    limit=100
                )

            elif trait_name == 'trophic_type':
                # Categorical trait search
                trophic_val = input.trophic_value()
                if not trophic_val:
                    logger.warning("No trophic type value selected")
                    return

                results = trait_db.query_species_by_trait(
                    trait_name=trait_name,
                    categorical_value=trophic_val
                )[:100]

            else:
                # General trait search
                results = trait_db.query_species_by_trait(
                    trait_name=trait_name
                )[:100]

            if results:
                results_df = pd.DataFrame(results)
                trait_search_results.set(results_df)
                logger.info(f"Found {len(results)} species with trait {trait_name}")
            else:
                trait_search_results.set(pd.DataFrame())
                logger.info(f"No species found with trait {trait_name}")

        except (DatabaseQueryError, TraitQueryError) as e:
            logger.error(f"Database/trait query error performing trait search: {e}")
            trait_search_results.set(pd.DataFrame())
        except (DatabaseError, TraitError) as e:
            logger.error(f"Database/trait error performing trait search: {e}")
            trait_search_results.set(pd.DataFrame())
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid trait search parameters: {e}")
            trait_search_results.set(pd.DataFrame())
        except Exception as e:
            logger.error(f"Unexpected error performing trait search: {e}")
            trait_search_results.set(pd.DataFrame())


app = App(app_ui, server)
