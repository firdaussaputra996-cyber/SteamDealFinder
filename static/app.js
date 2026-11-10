const form = document.querySelector("#searchForm");
const searchButton = document.querySelector("#searchButton");
const messageBar = document.querySelector("#messageBar");
const resultCount = document.querySelector("#resultCount");
const resultsGrid = document.querySelector("#resultsGrid");
const template = document.querySelector("#gameCardTemplate");
const genreSelect = document.querySelector("#genreTag");

function setMessage(message, isError = false) {
  messageBar.textContent = message;
  messageBar.classList.toggle("error", isError);
}

function buildQuery() {
  const params = new URLSearchParams();
  const fields = ["query", "tag_id", "min_price", "max_price", "min_discount"];

  for (const field of fields) {
    const input = form.elements[field];
    const value = input.value.trim();
    if (field === "min_discount" && (value === "" || Number(value) <= 0)) {
      continue;
    }
    if (value !== "") {
      params.set(field, value);
    }
  }

  return params;
}

async function loadGenres() {
  try {
    const response = await fetch("/api/genres");
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Gagal memuat genre.");
    }

    const genres = [...payload.genres].sort((a, b) =>
      a.name.localeCompare(b.name, "id")
    );

    for (const genre of genres) {
      const option = document.createElement("option");
      option.value = genre.tagid;
      option.textContent = genre.name;
      genreSelect.appendChild(option);
    }
  } catch (error) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Genre gagal dimuat";
    genreSelect.replaceChildren(option);
  }
}

function renderGames(games) {
  resultsGrid.innerHTML = "";

  for (const game of games) {
    const node = template.content.firstElementChild.cloneNode(true);
    const image = node.querySelector(".game-image");
    const title = node.querySelector(".game-title");
    const discount = node.querySelector(".discount-badge");
    const initialPrice = node.querySelector(".initial-price");
    const finalPrice = node.querySelector(".final-price");
    const steamLink = node.querySelector(".steam-link");

    image.src = game.header_image || "";
    image.alt = game.name;
    title.textContent = game.name;
    discount.textContent = game.discount_percent > 0 ? `-${game.discount_percent}%` : "Normal";
    initialPrice.textContent = game.display_initial_price || "";
    finalPrice.textContent = game.display_price;
    steamLink.href = game.store_url;

    resultsGrid.appendChild(node);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const minPrice = Number(form.elements.min_price.value || 0);
  const maxPrice = Number(form.elements.max_price.value || 0);

  if (maxPrice > 0 && minPrice > maxPrice) {
    setMessage("Harga minimum tidak boleh lebih besar dari harga maksimum.", true);
    return;
  }

  searchButton.disabled = true;
  resultCount.textContent = "Mencari";
  resultsGrid.innerHTML = "";
  setMessage("Mengambil data dari Steam...");

  try {
    const response = await fetch(`/api/search?${buildQuery().toString()}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Pencarian gagal.");
    }

    renderGames(payload.results);
    resultCount.textContent = `${payload.count} hasil`;
    setMessage(
      payload.count > 0
        ? `Ditemukan ${payload.count} hasil.`
        : "Tidak ada game yang cocok dengan kriteria."
    );
  } catch (error) {
    resultCount.textContent = "Error";
    setMessage(error.message, true);
  } finally {
    searchButton.disabled = false;
  }
});

loadGenres();
