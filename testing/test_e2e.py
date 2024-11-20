# write a test that sorts the table and asserts the order.
# sort default columns and custom sortable column
import os
import urllib.parse

import pytest
import selenium.webdriver.support.expected_conditions as ec
from assertpy import assert_that
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

pytest_plugins = ("pytester",)


@pytest.fixture
def driver(pytester):
    chrome_options = webdriver.ChromeOptions()
    if os.environ.get("CI", False):
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Remote(
        command_executor="http://127.0.0.1:4444", options=chrome_options
    )

    yield driver
    driver.quit()


@pytest.fixture
def path(pytester):
    def func(path="report.html", cmd_flags=None):
        cmd_flags = cmd_flags or []

        path = pytester.path.joinpath(path)
        pytester.runpytest("--html", path, *cmd_flags)

        # Begin workaround
        # See: https://github.com/pytest-dev/pytest/issues/10738
        path.chmod(0o755)
        for parent in path.parents:
            try:
                os.chmod(parent, 0o755)
            except PermissionError:
                continue
        # End workaround

        return path

    return func


def _encode_query_params(params):
    return urllib.parse.urlencode(params)


def _parse_result_table(driver):
    table = driver.find_element(By.ID, "results-table")
    headers = table.find_elements(By.CSS_SELECTOR, "thead th")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr.collapsible")
    table_data = []
    for row in rows:
        data_dict = {}

        cells = row.find_elements(By.TAG_NAME, "td")
        for header, cell in zip(headers, cells):
            data_dict[header.text.lower()] = cell.text

        table_data.append(data_dict)

    return table_data


def test_visible(pytester, path, driver):
    pytester.makepyfile(
        """
        def test_pass_one(): pass
        def test_pass_two(): pass
        """
    )

    driver.get(f"file:///reports{path()}")
    WebDriverWait(driver, 5).until(
        ec.visibility_of_all_elements_located((By.CSS_SELECTOR, "#results-table"))
    )
    result = driver.find_elements(By.CSS_SELECTOR, "tr.collapsible")
    assert_that(result).is_length(2)

    query_params = _encode_query_params({"visible": ""})
    driver.get(f"file:///reports{path()}?{query_params}")
    WebDriverWait(driver, 5).until(
        ec.visibility_of_all_elements_located((By.CSS_SELECTOR, "#results-table"))
    )
    result = driver.find_elements(By.CSS_SELECTOR, "tr.collapsible")
    assert_that(result).is_length(0)


def test_custom_sorting(pytester, path, driver):
    pytester.makeconftest(
        """
        def pytest_html_results_table_header(cells):
            cells.append(
                '<th class="sortable alpha" data-column-type="alpha">Alpha</th>'
            )

        def pytest_html_results_table_row(report, cells):
            data = report.nodeid.split("_")[-1]
            cells.append(f'<td class="col-alpha">{data}</td>')
    """
    )
    pytester.makepyfile(
        """
        def test_AAA(): pass
        def test_BBB(): pass
    """
    )
    query_params = _encode_query_params({"sort": "alpha"})
    driver.get(f"file:///reports{path()}?{query_params}")
    WebDriverWait(driver, 5).until(
        ec.visibility_of_all_elements_located((By.CSS_SELECTOR, "#results-table"))
    )

    rows = _parse_result_table(driver)
    assert_that(rows).is_length(2)
    assert_that(rows[0]["test"]).contains("AAA")
    assert_that(rows[0]["alpha"]).is_equal_to("AAA")
    assert_that(rows[1]["test"]).contains("BBB")
    assert_that(rows[1]["alpha"]).is_equal_to("BBB")

    driver.find_element(By.CSS_SELECTOR, "th[data-column-type='alpha']").click()
    # we might need some wait here to ensure sorting happened
    rows = _parse_result_table(driver)
    assert_that(rows).is_length(2)
    assert_that(rows[0]["test"]).contains("BBB")
    assert_that(rows[0]["alpha"]).is_equal_to("BBB")
    assert_that(rows[1]["test"]).contains("AAA")
    assert_that(rows[1]["alpha"]).is_equal_to("AAA")
