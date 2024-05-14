const slider = document.getElementById('timerSlider');
const sliderLabel = document.getElementById('sliderLabel');
function updateSliderLabel() {
  let m = " minute"
  const v = slider.value
  if (v > 1) {
    m += "s"
  }
  sliderLabel.textContent = slider.value + m
}
slider.addEventListener('input', () => updateSliderLabel(sliderLabel))
updateSliderLabel()

function getTimerString(tsDifference) {
  if (tsDifference <= 0) {
    return "Timer done"
  }

  const minutes = Math.floor(tsDifference / 1000 / 60);
  const seconds = Math.floor((tsDifference / 1000) % 60);

  const formattedMinutes = minutes.toString().padStart(2, ' ');
  const formattedSeconds = seconds.toString().padStart(2, '0');

  return `${formattedMinutes}:${formattedSeconds}`;
}

const timerDiv = document.getElementById("timerDiv")
if (timerDiv.classList.contains('running')) {
  const display = document.getElementById('timerDisplay');
  const tsMillis = Number(display.dataset.timestamp) * 1000
  const expires = new Date(tsMillis)
  function updateDisplay() {
    const now = new Date()
    const tsDifference = expires - now
    if (tsDifference < -2500) {
      timerDiv.classList.toggle("running", false)
    }
    display.textContent = getTimerString(tsDifference)
  }
  setInterval(updateDisplay, 1000)
  updateDisplay()
}
