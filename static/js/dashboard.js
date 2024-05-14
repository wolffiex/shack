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
slider.addEventListener('input', updateSliderLabel)
updateSliderLabel()

