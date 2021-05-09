const genericSort = (list, key, ascending) => {
  const sorted = list.sort((a, b) =>
    a[key] === b[key] ? 0 : a[key] === b[key] ? 1 : -1
  );

  if (ascending) {
    sorted.reverse();
  }
  return sorted;
};
