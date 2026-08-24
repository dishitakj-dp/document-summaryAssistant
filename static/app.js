const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const fileInfo = document.getElementById("fileInfo");
const controls = document.getElementById("controls");
const summarizeBtn = document.getElementById("summarizeBtn");
const summaryLength = document.getElementById("summaryLength");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loadingText");
const errorBox = document.getElementById("error");
const results = document.getElementById("results");
const summaryText = document.getElementById("summaryText");
const keyPoints = document.getElementById("keyPoints");
const details = document.getElementById("details");
const copyBtn = document.getElementById("copyBtn");

let extractedText = "";
let documentInfo = null;

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

function setLoading(active, text = "Processing document…") {
  loading.classList.toggle("hidden", !active);
  loadingText.textContent = text;
  summarizeBtn.disabled = active;
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 2);
  return `${(bytes / Math.pow(1024, index)).toFixed(1)} ${units[index]}`;
}

async function processFile(file) {
  clearError();
  results.classList.add("hidden");

  if (!file) return;

  const allowed = [".pdf", ".png", ".jpg", ".jpeg", ".webp"];
  const extension = "." + file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(extension)) {
    showError("Please upload a PDF or supported image file.");
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showError("The file is larger than 10 MB.");
    return;
  }

  fileInfo.textContent = `Selected: ${file.name} · ${formatBytes(file.size)}`;
  fileInfo.classList.remove("hidden");
  setLoading(true, "Extracting text from your document…");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/extract", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) throw new Error(data.detail || "Text extraction failed.");

    extractedText = data.text;
    documentInfo = data;

    controls.classList.remove("hidden");
    fileInfo.textContent =
      `Selected: ${data.filename} · ${formatBytes(file.size)} · ${data.extraction_method} · ${data.characters.toLocaleString()} characters`;
  } catch (error) {
    showError(error.message);
    controls.classList.add("hidden");
  } finally {
    setLoading(false);
  }
}

fileInput.addEventListener("change", (event) => processFile(event.target.files[0]));

["dragenter", "dragover"].forEach(type => {
  dropZone.addEventListener(type, event => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach(type => {
  dropZone.addEventListener(type, event => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", event => {
  processFile(event.dataTransfer.files[0]);
});

summarizeBtn.addEventListener("click", async () => {
  clearError();
  if (!extractedText) {
    showError("Please upload a document first.");
    return;
  }

  setLoading(true, "Generating your summary…");

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: extractedText,
        length: summaryLength.value
      })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Summary generation failed.");

    summaryText.textContent = data.summary;
    keyPoints.innerHTML = "";
    data.key_points.forEach(point => {
      const li = document.createElement("li");
      li.textContent = point;
      keyPoints.appendChild(li);
    });

    details.innerHTML = `
      <div class="detail"><span>File</span><span>${escapeHtml(documentInfo.filename)}</span></div>
      <div class="detail"><span>Extraction</span><span>${escapeHtml(documentInfo.extraction_method)}</span></div>
      <div class="detail"><span>Text</span><span>${documentInfo.characters.toLocaleString()} chars</span></div>
      <div class="detail"><span>Length</span><span>${escapeHtml(data.length)}</span></div>
    `;

    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(summaryText.textContent);
    copyBtn.textContent = "Copied!";
    setTimeout(() => copyBtn.textContent = "Copy summary", 1200);
  } catch {
    showError("Could not copy the summary.");
  }
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
}
