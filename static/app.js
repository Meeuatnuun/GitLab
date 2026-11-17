(() => {
  const form = document.querySelector("form");
  if (!form) return;

  const modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
  const fieldRows = Array.from(document.querySelectorAll(".field-row[data-modes]"));
  const diagrams = Array.from(document.querySelectorAll(".circuit-diagram"));
  const resultsCard = document.querySelector(".results-card");

  function selectedMode() {
    const checked = form.querySelector('input[name="mode"]:checked');
    return checked ? checked.value : null;
  }

  function sync() {
    const mode = selectedMode();
    if (!mode) return;

    fieldRows.forEach((row) => {
      const active = row.dataset.modes.split(/\s+/).includes(mode);
      row.hidden = !active;
      row.querySelectorAll("input, select").forEach((control) => {
        control.disabled = !active;
      });
    });

    diagrams.forEach((diagram) => {
      diagram.hidden = diagram.dataset.mode !== mode;
    });

    if (resultsCard) {
      const resultMode = resultsCard.dataset.mode;
      resultsCard.classList.toggle(
        "is-stale",
        Boolean(resultMode) && resultMode !== mode
      );
    }
  }

  modeInputs.forEach((input) => input.addEventListener("change", sync));
  sync();
})();
