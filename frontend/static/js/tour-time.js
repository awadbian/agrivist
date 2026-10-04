const timeForm = document.querySelector("[data-time-form]");
const timeInputs = document.querySelectorAll("input[name='selected_time']");
const participantsInput = document.getElementById("participants");
const summaryBox = document.querySelector("[data-booking-summary]");
const summaryTime = document.querySelector("[data-summary-time]");
const summaryTotal = document.querySelector("[data-summary-total]");

function getSelectedTime() {
    const checked = document.querySelector("input[name='selected_time']:checked");
    return checked ? checked.value : "";
}

function updateSummary() {
    if (!timeForm || !summaryBox || !summaryTime || !summaryTotal || !participantsInput) {
        return;
    }

    const selectedTime = getSelectedTime();
    const participants = Number(participantsInput.value);
    const price = Number(timeForm.dataset.price || 0);

    if (!selectedTime || !participants || participants <= 0) {
        summaryBox.hidden = true;
        return;
    }

    summaryTime.textContent = selectedTime;
    summaryTotal.textContent = `₪${price * participants}`;
    summaryBox.hidden = false;
}

timeInputs.forEach((input) => {
    input.addEventListener("change", () => {
        document.querySelectorAll(".time-option").forEach((option) => {
            const optionInput = option.querySelector("input[name='selected_time']");
            option.classList.toggle("selected", Boolean(optionInput && optionInput.checked));
        });
        updateSummary();
    });
});

if (participantsInput) {
    participantsInput.addEventListener("input", updateSummary);
}

updateSummary();
