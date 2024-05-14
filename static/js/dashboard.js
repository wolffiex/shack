function updateSliderLabel(sliderLabel) {
  let m = " minute"
  const v = slider.value
  if (v > 1) {
    m += "s"
  }
  sliderLabel.textContent = slider.value + m
}

function getTimerString(expires) {
  const now = new Date()
  const tsDifference = expires - now

  if (tsDifference <= 0) {
    return "Timer done"
  }

  const minutes = Math.floor(tsDifference / 1000 / 60);
  const seconds = Math.floor((tsDifference / 1000) % 60);

  const formattedMinutes = minutes.toString().padStart(2, ' ');
  const formattedSeconds = seconds.toString().padStart(2, '0');

  return `${formattedMinutes}:${formattedSeconds}`;
}

const slider = document.getElementById('timerSlider');
if (slider) {
  const sliderLabel = document.getElementById('sliderLabel');

  slider.addEventListener('input', () => updateSliderLabel(sliderLabel))
  updateSliderLabel()
}

const display = document.getElementById('timerDisplay');
console.log(display)
if (display) {
  const tsMillis = Number(display.dataset.timestamp) * 1000
  const expires = new Date(tsMillis)
  const updateDisplay = () => display.textContent = getTimerString(expires)
  setInterval(updateDisplay, 1000)
  updateDisplay()
}
