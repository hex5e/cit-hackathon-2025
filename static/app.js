const listContainer = document.getElementById("people-body");
const form = document.getElementById("person-form");
const errorMessage = form.querySelector(".error");
const columnCount = document.querySelectorAll("thead th").length;

const booleanFields = [
  "criminal_history",
  "addiction_history",
  "addiction_current",
  "disability",
  "mental_illness_history",
  "high_school_ed",
  "work_history",
  "higher_ed",
  "veteran",
  "dependents",
];

function formatBoolean(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  return value ? "Yes" : "No";
}

function formatText(value) {
  return value && value !== "" ? value : "—";
}

function formatZip(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return value;
}

async function fetchPeople() {
  const response = await fetch("/api/people");
  if (!response.ok) {
    throw new Error("Unable to load people");
  }
  const data = await response.json();
  return data.people;
}

function renderRows(people) {
  listContainer.innerHTML = "";
  if (people.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = columnCount;
    emptyCell.textContent = "No entries yet.";
    emptyCell.classList.add("empty");
    emptyRow.appendChild(emptyCell);
    listContainer.appendChild(emptyRow);
    return;
  }

  for (const person of people) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${person.id}</td>
      <td>${person.first_name}</td>
      <td>${person.last_name}</td>
      <td>${formatText(person.date_of_birth)}</td>
      <td>${formatText(person.address)}</td>
      <td>${formatZip(person.zip)}</td>
      <td>${formatBoolean(person.criminal_history)}</td>
      <td>${formatBoolean(person.addiction_history)}</td>
      <td>${formatBoolean(person.addiction_current)}</td>
      <td>${formatBoolean(person.disability)}</td>
      <td>${formatBoolean(person.mental_illness_history)}</td>
      <td>${formatBoolean(person.high_school_ed)}</td>
      <td>${formatBoolean(person.work_history)}</td>
      <td>${formatBoolean(person.higher_ed)}</td>
      <td>${formatBoolean(person.veteran)}</td>
      <td>${formatBoolean(person.dependents)}</td>
    `;
    listContainer.appendChild(row);
  }
}

async function refreshList() {
  try {
    const people = await fetchPeople();
    renderRows(people);
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = {};

  for (const [key, value] of formData.entries()) {
    payload[key] = typeof value === "string" ? value.trim() : value;
  }

  if (payload.zip && !/^[0-9]{5}$/.test(payload.zip)) {
    errorMessage.textContent = "ZIP must be empty or exactly 5 digits.";
    errorMessage.hidden = false;
    return;
  }

  for (const field of booleanFields) {
    if (!(field in payload)) {
      payload[field] = null;
    }
  }

  errorMessage.hidden = true;

  try {
    const response = await fetch("/api/people", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json();
      throw new Error(errorBody.error ?? "Unable to save");
    }

    form.reset();
    resetTriStateRadios();
    await refreshList();
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  }
});

function setupTriStateRadios() {
  const radios = document.querySelectorAll('.choice-row input[type="radio"]');
  radios.forEach((input) => {
    input.dataset.checked = "false";
    input.addEventListener("click", (event) => {
      if (input.dataset.checked === "true") {
        input.checked = false;
        input.dataset.checked = "false";
        event.preventDefault();
        return;
      }

      document
        .querySelectorAll(`input[name="${input.name}"]`)
        .forEach((radio) => {
          radio.dataset.checked = radio === input ? "true" : "false";
        });
    });
  });
}

function resetTriStateRadios() {
  document
    .querySelectorAll('.choice-row input[type="radio"]')
    .forEach((input) => {
      input.dataset.checked = "false";
    });
}

setupTriStateRadios();
refreshList();
