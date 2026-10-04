const modal = document.getElementById("pepperModal");
const modalImage = document.getElementById("modalImage");
const modalTitle = document.getElementById("modalTitle");
const modalScientific = document.getElementById("modalScientific");
const modalOrigin = document.getElementById("modalOrigin");
const modalDescription = document.getElementById("modalDescription");
const modalExtra = document.getElementById("modalExtra");
const modalDetailList = document.getElementById("modalDetailList");
const modalTips = document.getElementById("modalTips");

function readDetail(card, selector) {
    const node = card.querySelector(selector);
    return node ? node.textContent.trim() : "";
}

function renderDetailList(details) {
    modalDetailList.innerHTML = "";

    details.forEach((detail) => {
        if (!detail.value) {
            return;
        }

        const item = document.createElement("div");
        item.className = "detail-item";

        const label = document.createElement("span");
        label.className = "detail-label";
        label.textContent = detail.label;

        const value = document.createElement("div");
        value.className = "detail-value";
        value.textContent = detail.value;

        item.append(label, value);
        modalDetailList.appendChild(item);
    });
}

document.querySelectorAll(".image-open").forEach((button) => {
    button.addEventListener("click", () => {
        const card = button.closest(".pepper-card");
        const imageUrl = readDetail(card, ".detail-image");
        const name = readDetail(card, ".detail-name");

        if (!name) {
            return;
        }

        modalTitle.textContent = name;
        modalScientific.textContent = readDetail(card, ".detail-scientific");
        modalOrigin.textContent = "מקור: " + readDetail(card, ".detail-origin");
        modalDescription.textContent = readDetail(card, ".detail-description");
        modalExtra.textContent = readDetail(card, ".detail-extra");
        modalTips.textContent = readDetail(card, ".detail-tips");

        renderDetailList([
            { label: "סטטוס", value: readDetail(card, ".detail-status") },
            { label: "מידע ריסוס", value: readDetail(card, ".detail-spray") },
            { label: "צרכי השקיה", value: readDetail(card, ".detail-watering") },
            { label: "צרכי שמש", value: readDetail(card, ".detail-sunlight") },
            { label: "סוג אדמה", value: readDetail(card, ".detail-soil") },
            { label: "טמפרטורה מתאימה", value: readDetail(card, ".detail-temperature") },
            { label: "עונה", value: readDetail(card, ".detail-season") },
            { label: "תדירות השקיה", value: readDetail(card, ".detail-irrigation-frequency") },
            { label: "כמות מים", value: readDetail(card, ".detail-water-amount") },
            { label: "עונת קטיף", value: readDetail(card, ".detail-harvest-season") },
            { label: "ימים עד קטיף", value: readDetail(card, ".detail-days-to-harvest") },
            { label: "סימני מוכנות לקטיף", value: readDetail(card, ".detail-harvest-signs") },
            { label: "אחסון לאחר קטיף", value: readDetail(card, ".detail-storage-tips") },
            { label: "אזהרות", value: readDetail(card, ".detail-warnings") },
        ]);

        modalImage.src = imageUrl || "";
        modalImage.alt = name;
        modalImage.style.display = imageUrl ? "block" : "none";

        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
    });
});

function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
}

document.getElementById("modalClose").addEventListener("click", closeModal);

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        closeModal();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeModal();
    }
});

const searchInput = document.getElementById("pepperSearch");

if (searchInput) {
    searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim().toLowerCase();

        document.querySelectorAll(".pepper-card").forEach((card) => {
            const haystack = (card.dataset.search || "").toLowerCase();
            card.style.display = haystack.includes(query) ? "" : "none";
        });
    });
}