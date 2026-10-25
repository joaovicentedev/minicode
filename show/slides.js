function formatElapsed(seconds) {
  const whole = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(whole / 60)).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`;
}

function moveSlide(index, delta, count) {
  return Math.min(Math.max(index + delta, 0), count - 1);
}

function createPresentation(doc, clock, scheduler) {
  const slides = [...doc.querySelectorAll(".slide")];
  const counter = doc.querySelector("#slide-count");
  const timer = doc.querySelector("#timer");
  const progress = doc.querySelector("#progress");
  const prev = doc.querySelector("#previous");
  const next = doc.querySelector("#next");
  let index = 0;
  let started = clock();

  function render() {
    slides.forEach((slide, position) => {
      slide.hidden = position !== index;
      slide.setAttribute("aria-hidden", String(position !== index));
    });
    counter.textContent = `${String(index + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;
    progress.style.width = `${((index + 1) / slides.length) * 100}%`;
    prev.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    doc.title = `MiniCode — ${slides[index].dataset.title}`;
  }

  function navigate(delta) {
    index = moveSlide(index, delta, slides.length);
    render();
  }

  function updateTimer() {
    timer.textContent = formatElapsed((clock() - started) / 1000);
  }

  function handleKey(event) {
    if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(event.key)) {
      event.preventDefault();
      navigate(1);
    } else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(event.key)) {
      event.preventDefault();
      navigate(-1);
    } else if (event.key === "Home") {
      event.preventDefault();
      navigate(-slides.length);
    } else if (event.key === "End") {
      event.preventDefault();
      navigate(slides.length);
    } else if (event.key.toLowerCase() === "r") {
      started = clock();
      updateTimer();
    }
  }

  doc.addEventListener("keydown", handleKey);
  prev.addEventListener("click", () => navigate(-1));
  next.addEventListener("click", () => navigate(1));
  scheduler(updateTimer, 1000);
  render();
  updateTimer();
  return { navigate, render, updateTimer, handleKey };
}

if (typeof document !== "undefined") {
  createPresentation(document, () => performance.now(), setInterval);
}

if (typeof module !== "undefined") {
  module.exports = { formatElapsed, moveSlide, createPresentation };
}
