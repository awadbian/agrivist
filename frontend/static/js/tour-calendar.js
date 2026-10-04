const calendarForm = document.querySelector("[data-calendar-form]");
const calendarGrid = document.querySelector("[data-calendar-grid]");
const calendarTitle = document.querySelector("[data-calendar-title]");
const selectedDateInput = document.getElementById("selectedDate");
const selectedDateSummary = document.querySelector("[data-selected-date-summary]");
const prevButton = document.querySelector("[data-calendar-prev]");
const nextButton = document.querySelector("[data-calendar-next]");

const monthNames = [
    "ינואר",
    "פברואר",
    "מרץ",
    "אפריל",
    "מאי",
    "יוני",
    "יולי",
    "אוגוסט",
    "ספטמבר",
    "אוקטובר",
    "נובמבר",
    "דצמבר",
];

const dayNames = [
    "יום ראשון",
    "יום שני",
    "יום שלישי",
    "יום רביעי",
    "יום חמישי",
    "יום שישי",
    "יום שבת",
];

function parseLocalDate(value) {
    const parts = (value || "").split("-").map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) {
        return null;
    }
    return new Date(parts[0], parts[1] - 1, parts[2]);
}

function toDateValue(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function renderSelectedSummary() {
    const selectedDate = parseLocalDate(selectedDateInput.value);
    if (!selectedDate) {
        selectedDateSummary.hidden = true;
        selectedDateSummary.textContent = "";
        return;
    }

    const dayName = dayNames[selectedDate.getDay()];
    selectedDateSummary.textContent = `תאריך נבחר: ${dayName}, ${selectedDate.getDate()} ב${monthNames[selectedDate.getMonth()]} ${selectedDate.getFullYear()}`;
    selectedDateSummary.hidden = false;
}

if (calendarForm && calendarGrid && calendarTitle && selectedDateInput) {
    const today = parseLocalDate(calendarForm.dataset.today) || new Date();
    const selectedDate = parseLocalDate(selectedDateInput.value);
    let visibleMonth = new Date(
        selectedDate ? selectedDate.getFullYear() : today.getFullYear(),
        selectedDate ? selectedDate.getMonth() : today.getMonth(),
        1
    );

    function renderCalendar() {
        calendarGrid.innerHTML = "";
        calendarTitle.textContent = `${monthNames[visibleMonth.getMonth()]} ${visibleMonth.getFullYear()}`;

        const firstOfMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
        const calendarStart = new Date(firstOfMonth);
        calendarStart.setDate(firstOfMonth.getDate() - firstOfMonth.getDay());

        for (let week = 0; week < 6; week += 1) {
            for (let weekday = 6; weekday >= 0; weekday -= 1) {
                const date = new Date(calendarStart);
                date.setDate(calendarStart.getDate() + (week * 7) + weekday);

                if (date.getMonth() !== visibleMonth.getMonth()) {
                    const spacer = document.createElement("span");
                    spacer.className = "calendar-spacer";
                    calendarGrid.appendChild(spacer);
                    continue;
                }

                const value = toDateValue(date);
                const button = document.createElement("button");
                button.className = "calendar-day";
                button.type = "button";
                button.textContent = String(date.getDate());
                button.disabled = date < today;

                if (selectedDateInput.value === value) {
                    button.classList.add("selected");
                }

                button.addEventListener("click", () => {
                    selectedDateInput.value = value;
                    renderCalendar();
                    renderSelectedSummary();
                });

                calendarGrid.appendChild(button);
            }
        }
    }

    prevButton.addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
        renderCalendar();
    });

    nextButton.addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
        renderCalendar();
    });

    renderCalendar();
    renderSelectedSummary();
}
