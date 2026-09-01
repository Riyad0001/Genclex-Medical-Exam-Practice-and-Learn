(function () {
  function parseObjects(select) {
    try {
      return JSON.parse(select.dataset.resourceObjects || "{}");
    } catch (error) {
      return {};
    }
  }

  function fillObjectSelect(typeSelect, objectSelect) {
    const objectMap = parseObjects(objectSelect);
    const selectedType = typeSelect.value;
    const selectedObject = objectSelect.value;
    const options = objectMap[selectedType] || [];

    objectSelect.replaceChildren(new Option("---------", ""));

    options.forEach(function (item) {
      objectSelect.appendChild(new Option(item[1], item[0]));
    });

    if (selectedObject && options.some(function (item) { return item[0] === selectedObject; })) {
      objectSelect.value = selectedObject;
    }
  }

  function initRow(row) {
    const typeSelect = row.querySelector("select.js-resource-content-type");
    const objectSelect = row.querySelector("select.js-resource-object-id");

    if (!typeSelect || !objectSelect || typeSelect.dataset.resourceBound === "true") {
      return;
    }

    typeSelect.dataset.resourceBound = "true";
    typeSelect.addEventListener("change", function () {
      objectSelect.value = "";
      fillObjectSelect(typeSelect, objectSelect);
    });
    fillObjectSelect(typeSelect, objectSelect);
  }

  function initAll() {
    document.querySelectorAll("select.js-resource-content-type").forEach(function (select) {
      initRow(select.closest("tr") || select.closest(".form-row") || document);
    });
  }

  document.addEventListener("DOMContentLoaded", initAll);
  document.addEventListener("formset:added", function (event) {
    initRow(event.target);
  });
})();
