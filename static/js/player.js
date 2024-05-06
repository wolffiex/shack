const FRAME_DURATION = 100
export class Player {
  constructor(playerID, controlsID, frameCount) {
    this.playerDiv = document.getElementById(playerID)
    this.frameCount = frameCount
    this.imgs = this.playerDiv.querySelectorAll('img');
    // this.imgMap = new Map([...this.imgs].map((el, n) => [el, n]))
    this.controlsDiv = document.getElementById(controlsID)
    const pauseButton = this.controlsDiv.querySelector('button[name="play-pause"]');
    const inputField = this.controlsDiv.querySelector('input[name="inputField"]');

    pauseButton.addEventListener('click', () => {
      this.toggle()
    });

    inputField.addEventListener('input', (event) => {
      this.frameNum = inputField.value - 1
      this.pause()
    });
    document.addEventListener('keydown', (event) => {
      if (event.code === 'Space') {
        this.toggle()
      } else if (event.code === 'ArrowLeft') {
        this.pause()
        this.frameNum -= 1
        if (this.frameNum < 0) this.frameNum = this.frameCount - 1
        this.sync()
      } else if (event.code === 'ArrowRight') {
        this.pause()
        this.frameNum += 1
        this.sync()
      }
    });

    this.controls = { pauseButton, inputField }
    this.frameNum = 0
    this.pause()
  }

  toggle() {
    if (this.playing) this.pause()
    else this.play()
  }

  play() {
    this.playing = true
    this.lastFrameTime = performance.now()
    this.sync()
    this.onAnimationFrame()
  }

  pause() {
    this.playing = false
    this.lastFrameTime = performance.now()
    this.sync()
  }

  // Must be explictly bound for callback
  onAnimationFrame = () => {
    if (!this.playing) return
    const currentTime = performance.now()
    const frameElapsed = currentTime - this.lastFrameTime
    if (frameElapsed > FRAME_DURATION) {
      this.advanceFrame()
    }
    requestAnimationFrame(this.onAnimationFrame);
  }

  advanceFrame() {
    this.lastFrameTime = performance.now()
    this.frameNum++
    this.sync()
  }

  sync() {
    if (this.playing) {
      this.controlsDiv.classList.add('playing')
    } else {
      this.controlsDiv.classList.remove('playing')
    }
    this.frameNum = this.frameNum % this.frameCount
    const shownImgs = this.playerDiv.querySelectorAll('.shown');
    for (const img of shownImgs) {
      img.classList.remove("shown")
    }
    this.imgs[this.frameNum].classList.add("shown")
    this.controls.inputField.value = this.frameNum + 1
  }
}
