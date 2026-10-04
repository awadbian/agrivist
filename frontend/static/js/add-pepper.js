/* =========================================================
   Add Pepper Page JavaScript
   Keeps small form behavior out of the HTML template.
   ========================================================= */

const heatLevelInput = document.getElementById("heat_level_value");
const scovilleInput = document.getElementById("scoville_level");
const pepperForm = document.querySelector(".pepper-form-card");

function syncScovilleFallback() {
    if (!heatLevelInput || !scovilleInput) {
        return;
    }

    const value = heatLevelInput.value.trim();
    if (!scovilleInput.value.trim()) {
        scovilleInput.value = value;
    }
}

if (heatLevelInput) {
    heatLevelInput.addEventListener("input", () => {
        const parsedValue = Number(heatLevelInput.value);
        if (Number.isNaN(parsedValue)) {
            return;
        }

        if (parsedValue < 0) {
            heatLevelInput.value = "0";
        } else if (parsedValue > 5) {
            heatLevelInput.value = "5";
        }

        if (scovilleInput) {
            scovilleInput.value = heatLevelInput.value.trim();
        }
    });
}

if (pepperForm) {
    pepperForm.addEventListener("submit", syncScovilleFallback);
}
