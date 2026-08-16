from app.engine.learn_categories import matching_character_categories


def test_single_stored_category_is_unchanged():
    assert matching_character_categories("Sports") == frozenset({"Sports"})
    assert matching_character_categories("Movies") == frozenset({"Movies"})


def test_display_aliases_map_to_stored_values():
    assert matching_character_categories("Science") == frozenset({"Scientists"})
    assert matching_character_categories("Politics") == frozenset({"Politicians"})


def test_group_aliases_use_existing_stored_categories():
    fictional = matching_character_categories("Fictional Characters")
    assert "Movies" in fictional
    assert "Anime" in fictional
    assert "Sports" not in fictional
    famous = matching_character_categories("Famous People")
    assert "Sports" in famous
    assert "Movies" not in famous


def test_missing_data_worlds_are_literal_filters():
    assert matching_character_categories("Internet & Social Media") == frozenset(
        {"Internet & Social Media"}
    )
    assert matching_character_categories("World / Geography") == frozenset(
        {"World / Geography"}
    )


def test_blank_category_means_no_filter():
    assert matching_character_categories(None) is None
    assert matching_character_categories("  ") is None
