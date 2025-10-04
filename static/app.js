const listContainer = document.getElementById("people-body");
const form = document.getElementById("person-form");
const errorMessage = form.querySelector(".error");

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
    emptyCell.colSpan = 3;
    emptyCell.textContent = "No entries yet.";
    emptyCell.classList.add("empty");
    emptyRow.appendChild(emptyCell);
    listContainer.appendChild(emptyRow);
    return;
  }

  for (const person of people) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${person.first_name}</td>
      <td>${person.last_name}</td>
      <td>${person.zip_code}</td>
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
  const payload = Object.fromEntries(formData.entries());

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
    await refreshList();
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  }
});

refreshList();
