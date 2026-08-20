const form = document.getElementById("estimate-form");
const neighborhoodSelect = document.getElementById("neighborhood");
const draftButton = document.getElementById("draft-button");
const formErrors = document.getElementById("form-errors");
const modelMeta = document.getElementById("model-meta");

const resultPlaceholder = document.getElementById("result-placeholder");
const resultContent = document.getElementById("result-content");
const resultValue = document.getElementById("result-value");
const resultLow = document.getElementById("result-low");
const resultHigh = document.getElementById("result-high");
const rangeBarFill = document.querySelector(".range-bar-fill");
const factorsEl = document.getElementById("factors");
const resultFootnote = document.getElementById("result-footnote");

const callouts = document.getElementById("callouts");
const calloutArea = document.getElementById("callout-area");
const calloutGrade = document.getElementById("callout-grade");

const money = (n) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

async function loadStaticAssets() {
  try {
    const [neighborhoods, metrics] = await Promise.all([
      fetch("assets/neighborhoods.json").then((r) => r.json()),
      fetch("assets/model_metrics.json").then((r) => r.json()),
    ]);

    neighborhoodSelect.innerHTML = neighborhoods
      .map((n) => `<option value="${n}">${n}</option>`)
      .join("");

    modelMeta.textContent = `${metrics.model_name} · R² ${metrics.r2.toFixed(3)} · MAE ${money(Math.round(metrics.mae))}`;
  } catch (err) {
    modelMeta.textContent = "model metadata unavailable";
    neighborhoodSelect.innerHTML = `<option value="">(load failed — type won't matter, backend rejects unknowns anyway)</option>`;
  }
}

function collectPayload() {
  const data = new FormData(form);
  return {
    neighborhood: neighborhoodSelect.value,
    sqft_living: Number(data.get("sqft_living")),
    lot_size_sqft: Number(data.get("lot_size_sqft")),
    bedrooms: Number(data.get("bedrooms")),
    bathrooms: Number(data.get("bathrooms")),
    floors: Number(data.get("floors")),
    year_built: Number(data.get("year_built")),
    renovated: document.getElementById("renovated").checked ? "Y" : "N",
    condition: Number(data.get("condition")),
    grade: Number(data.get("grade")),
    garage: document.getElementById("garage").checked ? "Y" : "N",
    basement: document.getElementById("basement").checked ? "Y" : "N",
    pool: document.getElementById("pool").checked ? "Y" : "N",
    school_score: Number(data.get("school_score")),
  };
}

function clearFieldErrors() {
  formErrors.textContent = "";
  form.querySelectorAll(".field-invalid").forEach((el) => el.classList.remove("field-invalid"));
}

function showFieldErrors(fields) {
  const messages = Object.entries(fields).map(([field, msg]) => {
    const input = document.getElementById(field);
    if (input) input.classList.add("field-invalid");
    return `${field.replace(/_/g, " ")}: ${msg}`;
  });
  formErrors.textContent = messages.join(" · ");
}

function renderResult(data) {
  resultPlaceholder.hidden = true;
  resultContent.hidden = false;

  resultValue.textContent = data.estimated_value_formatted;
  resultLow.textContent = money(data.range_low);
  resultHigh.textContent = money(data.range_high);

  const span = data.range_high - data.range_low;
  const pos = span > 0 ? ((data.estimated_value - data.range_low) / span) * 100 : 50;
  rangeBarFill.style.clipPath = `inset(0 ${100 - pos}% 0 0)`;

  factorsEl.innerHTML = data.top_factors
    .map(
      (f) => `
        <div class="factor-row">
          <span class="factor-label">${f.label}</span>
          <div class="factor-bar-track"><div class="factor-bar-fill" style="width:${f.importance_pct}%"></div></div>
          <span class="factor-pct">${f.importance_pct}%</span>
        </div>`
    )
    .join("");

  resultFootnote.textContent = `${data.model_name} v${data.model_version} · range is the point estimate ± the model's held-out RMSE`;

  calloutArea.textContent = `${document.getElementById("sqft_living").value} sqft`;
  calloutGrade.textContent = `grade ${document.getElementById("grade").value} / 10`;
  callouts.style.opacity = "1";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearFieldErrors();
  draftButton.disabled = true;
  draftButton.textContent = "Drafting…";

  try {
    const res = await fetch(`${API_BASE_URL}/estimate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectPayload()),
    });
    const body = await res.json();

    if (!res.ok) {
      showFieldErrors(body.fields || { form: body.error || "Request failed." });
      return;
    }
    renderResult(body);
  } catch (err) {
    formErrors.textContent = "Could not reach the estimator API. Is the backend running?";
  } finally {
    draftButton.disabled = false;
    draftButton.textContent = "Draft the estimate";
  }
});

loadStaticAssets();
