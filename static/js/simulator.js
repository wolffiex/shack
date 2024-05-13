const container = document.getElementById('container');

function loadWebPImage() {
  return new Promise((resolve, reject) => {
    const webpImage = new Image();
    webpImage.width = 640
    webpImage.height = 320
    webpImage.onload = () => {
      resolve(webpImage);
    };
    webpImage.onerror = (error) => {
      reject(error);
    };
    const cacheBuster = Date.now();
    
    // Append the cache buster to the image URL
    webpImage.src = `/pushbyt/v1/preview.webp?t=${cacheBuster}`;
  });
}

function replaceImage(img) {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
  container.appendChild(img);
  console.log("Placed img")
  prepNextImage()
}

function prepNextImage() {
  let nextImage = null
  setTimeout(() => {
    console.log("Load next")
    loadWebPImage()
      .then((webpImage) => {
        nextImage = webpImage
      })
  }, 10000)
  setTimeout(() => replaceImage(nextImage), 15000)
}

// Usage
loadWebPImage()
  .then((webpImage) => {
    // WebP image loaded successfully
    console.log('WebP image loaded');
    // Append the image to the DOM or perform any other actions
    replaceImage(webpImage)
  })
  .catch((error) => {
    // Error occurred while loading the WebP image
    console.error('Error loading WebP image:', error);
  });

function generate() {
  fetch("/pushbyt/command/generate")
    .then(response => response.text())
    .then(text =>
      console.log("Generation result: " + text)
    )
}

generate()
setInterval(generate, 60000)
