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
