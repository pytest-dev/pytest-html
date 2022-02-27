const dispatchEvent = (type, detail) => {
  const newEvent = new CustomEvent(type, { detail });

  document.dispatchEvent(newEvent);
};

const doSort = (type) => {
  const newSortType = localStorage.getItem('sort') !== type;
  const currentAsc = JSON.parse(localStorage.getItem('sortAsc'));
  const ascending = newSortType ? true : !currentAsc;
  localStorage.setItem('sort', type);
  localStorage.setItem('sortAsc', ascending);
  dispatchEvent('sort', { type, ascending });
};

document.addEventListener('sort', (e) => {
  const { type, ascending } = e.detail;
  const sortedList = genericSort(renderData.tests, type, ascending);
  renderData.tests = sortedList;
  redraw();
});

const doFilter = (type, apply) => {
  const currentFilter = [
    ...new Set(JSON.parse(localStorage.getItem('filter'))),
  ];
  if (apply) {
    currentFilter.push(type);
  } else {
    const index = currentFilter.indexOf(type);
    currentFilter.splice(index, 1);
  }
  localStorage.setItem('filter', JSON.stringify(currentFilter));
  const filteredSubset = [];
  if (currentFilter.length) {
    currentFilter.forEach((filter) => {
      filteredSubset.push(
        ...jsonData.tests.filter(({ outcome }) => outcome === filter)
      );
    });
    renderData.tests = filteredSubset;
  } else {
    renderData.tests = jsonData.tests;
  }
  redraw();
};
