"""
Reusable UI components for the Marine & Biodiversity Data Explorer.

This module provides helper functions to create consistent UI elements.
"""

from shiny import ui
from typing import Dict, List


def create_species_search_panel(country_codes: List[str]):
    """
    Create the species search panel with improved layout.

    Args:
        country_codes: List of country codes for the filter dropdown

    Returns:
        Shiny UI div containing the search panel
    """
    return ui.div(
        ui.h4("🔍 Species Search"),
        ui.input_text(
            "species_query",
            "Species Name",
            placeholder="e.g., Fucus vesiculosus",
        ),
        ui.input_select(
            "country",
            "Country Filter (optional)",
            choices=country_codes,
            selected="",
        ),
        ui.input_checkbox(
            "size_filter",
            "Only show records with size data",
            value=False,
        ),
        ui.div(
            ui.input_action_button(
                "search_btn",
                "🔍 Search",
                class_="btn btn-primary",
            ),
            ui.input_action_button(
                "clear_btn",
                "🗑️ Clear",
                class_="btn btn-secondary",
            ),
            class_="btn-group mt-2",
        ),
        class_="sidebar-card",
    )


def create_database_checkboxes(enable_previews_value: bool = False):
    """
    Create database selection checkboxes in an improved grid layout.

    Args:
        enable_previews_value: Whether to enable API previews by default

    Returns:
        Shiny UI div containing database checkboxes
    """
    databases = [
        ("bulk_db_gbif", "GBIF", "Global Biodiversity Information Facility", "preview_gbif", True),
        ("bulk_db_shark", "SHARK", "Swedish Ocean Archive (WoRMS/OBIS)", "preview_shark", False),
        ("bulk_db_obis", "OBIS", "Ocean Biodiversity Information System", "preview_obis", False),
        ("bulk_db_algaebase", "AlgaeBase", "Algal Taxonomy Database", "preview_algaebase", False),
        ("bulk_db_fwe", "FWE", "Freshwater Ecology Database", "preview_fwe", False),
    ]

    checkbox_items = []
    for db_id, db_name, db_desc, preview_id, default_value in databases:
        checkbox_items.append(
            ui.div(
                ui.div(
                    ui.row(
                        ui.column(
                            8,
                            ui.input_checkbox(db_id, db_name, value=default_value),
                            ui.div(db_desc, class_="text-muted text-small"),
                        ),
                        ui.column(
                            4,
                            ui.div(
                                ui.output_text(preview_id),
                                class_="text-muted text-small text-center",
                            ),
                        ),
                    ),
                ),
                class_="db-item mb-1",
            )
        )

    return ui.div(
        ui.h5("Select Databases to Query"),
        ui.input_checkbox(
            "enable_previews",
            "Enable API previews",
            value=enable_previews_value,
        ),
        ui.div(
            ui.div(
                *checkbox_items,
                class_="db-grid",
            ),
        ),
    )


def create_bulk_analysis_panel():
    """
    Create the bulk analysis panel with improved layout.

    Returns:
        Shiny UI div containing the bulk analysis panel
    """
    return ui.div(
        ui.h4("📊 Bulk Analysis"),
        ui.p(
            "Upload an Excel file with species names to analyze multiple species at once.",
            class_="text-muted text-small mb-2",
        ),
        ui.input_file(
            "species_file",
            "Upload Excel File (.xlsx)",
            accept=".xlsx",
        ),
        ui.input_select(
            "species_column",
            "Species Column",
            choices={"0": "Column 1"},
            selected="0",
        ),
        create_database_checkboxes(),
        ui.div(
            ui.input_action_button(
                "analyze_btn",
                "📊 Analyze All Species",
                class_="btn btn-success",
            ),
            ui.input_action_button(
                "analyze_first_btn",
                "🔬 Analyze First Species",
                class_="btn btn-primary",
            ),
            ui.input_action_button(
                "cancel_btn",
                "⛔ Cancel Analysis",
                class_="btn btn-danger",
            ),
            class_="btn-group mt-2",
        ),
        class_="sidebar-card",
    )


def create_button_group(buttons: List[Dict]):
    """
    Create a responsive button group.

    Args:
        buttons: List of button dictionaries with keys: id, label, class

    Returns:
        Shiny UI div containing button group
    """
    button_elements = []
    for btn in buttons:
        button_elements.append(
            ui.input_action_button(
                btn["id"],
                btn["label"],
                class_=btn.get("class", "btn btn-primary"),
            )
        )

    return ui.div(*button_elements, class_="btn-group")


def create_stat_card(title: str, output_id: str, icon: str = "📊"):
    """
    Create a statistics card with consistent styling.

    Args:
        title: Card title
        output_id: Shiny output ID
        icon: Emoji icon for the card

    Returns:
        Shiny UI div containing the stat card
    """
    return ui.div(
        ui.h5(f"{icon} {title}"),
        ui.output_text(output_id),
        class_="stat-card",
    )


def create_dashboard_card(content, title: str = None):
    """
    Create a dashboard card with optional title.

    Args:
        content: UI content to display in the card
        title: Optional title for the card

    Returns:
        Shiny UI div containing the dashboard card
    """
    elements = []
    if title:
        elements.append(ui.h4(title, class_="mb-2"))
    elements.append(content)

    return ui.div(*elements, class_="dashboard-card")


def create_empty_state(icon: str, title: str, subtitle: str):
    """
    Create an empty state placeholder.

    Args:
        icon: Emoji icon
        title: Main message
        subtitle: Subtitle message

    Returns:
        Shiny UI div containing the empty state
    """
    return ui.div(
        ui.div(icon, class_="empty-state-icon"),
        ui.div(title, class_="empty-state-text"),
        ui.div(subtitle, class_="empty-state-subtext"),
        class_="empty-state",
    )


def create_section_header(title: str, icon: str = "", subtitle: str = None):
    """
    Create a section header with optional icon and subtitle.

    Args:
        title: Section title
        icon: Optional emoji icon
        subtitle: Optional subtitle

    Returns:
        Shiny UI div containing the section header
    """
    elements = [ui.h4(f"{icon} {title}" if icon else title)]
    if subtitle:
        elements.append(ui.p(subtitle, class_="text-muted text-small"))

    return ui.div(*elements, class_="mb-2")


def create_help_tooltip(text: str, tooltip: str):
    """
    Create text with a help tooltip.

    Args:
        text: Display text
        tooltip: Tooltip content

    Returns:
        Shiny UI span with tooltip
    """
    return ui.span(
        text,
        ui.span("?", class_="help-icon", title=tooltip),
    )


def create_trait_search_panel():
    """
    Create the trait search panel for querying species by traits.

    Returns:
        Shiny UI div with trait search controls
    """
    return ui.div(
        ui.h4("🔬 Trait Search"),
        ui.p(
            "Search for species by trait values. Query the trait ontology database with "
            "morphological, ecological, and trophic characteristics.",
            class_="help-text"
        ),
        ui.input_select(
            "trait_name",
            "Trait",
            choices={
                "": "Select a trait...",
                "biovolume": "Biovolume (µm³)",
                "carbon_content": "Carbon content (pg)",
                "trophic_type": "Trophic type",
                "geometric_shape": "Geometric shape",
                "mobility": "Mobility",
                "feeding_method": "Feeding method",
                "typical_abundance": "Typical abundance",
                "environmental_position": "Environmental position"
            }
        ),
        ui.panel_conditional(
            "input.trait_name === 'biovolume' || input.trait_name === 'carbon_content'",
            ui.input_numeric("trait_min_value", "Minimum value", value=None, min=0),
            ui.input_numeric("trait_max_value", "Maximum value", value=None, min=0),
        ),
        ui.panel_conditional(
            "input.trait_name === 'trophic_type'",
            ui.input_select(
                "trophic_value",
                "Trophic type",
                choices={
                    "": "Select...",
                    "AU": "Autotroph (AU)",
                    "HE": "Heterotroph (HE)",
                    "MI": "Mixotroph (MI)"
                }
            ),
        ),
        ui.div(
            ui.input_action_button(
                "trait_search_btn",
                "🔍 Search by Trait",
                class_="btn-primary btn-block mt-2"
            ),
            class_="mt-2",
        ),
        ui.output_text("trait_search_results_count"),
        class_="sidebar-card mt-3",
    )


def create_trait_info_panel():
    """
    Create the trait information display panel.

    Returns:
        Shiny UI div for displaying trait information
    """
    return ui.div(
        ui.h5("🔬 Trait Information"),
        ui.output_text("trait_info_text"),
        class_="stat-card mt-3",
    )
