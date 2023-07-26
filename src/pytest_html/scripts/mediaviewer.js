class MediaViewer {
    constructor(assets) {
        this.assets = assets
        this.index = 0
    }

    nextActive() {
        this.index = this.index === this.assets.length - 1 ? 0 : this.index + 1
        return [this.activeFile, this.index]
    }

    prevActive() {
        this.index = this.index === 0 ? this.assets.length - 1 : this.index -1
        return [this.activeFile, this.index]
    }

    get currentIndex() {
        return this.index
    }

    get activeFile() {
        return this.assets[this.index]
    }
}


const setup = (resultBody, assets) => {
    if (!assets.length) {
        resultBody.querySelector('.media').classList.add('hidden')
        return
    }

    const mediaViewer = new MediaViewer(assets)
    const leftArrow = resultBody.querySelector('.media-container__nav--left')
    const rightArrow = resultBody.querySelector('.media-container__nav--right')
    const mediaName = resultBody.querySelector('.media__name')
    const counter = resultBody.querySelector('.media__counter')
    const imageEl = resultBody.querySelector('img')
    const sourceEl = resultBody.querySelector('source')
    const videoEl = resultBody.querySelector('video')

    const setImg = (media, index) => {
        if (media?.format_type === 'image') {
            imageEl.src = media.path

            imageEl.classList.remove('hidden')
            videoEl.classList.add('hidden')
        } else if (media?.format_type === 'video') {
            sourceEl.src = media.path

            videoEl.classList.remove('hidden')
            imageEl.classList.add('hidden')
        }

        mediaName.innerText = media?.name
        counter.innerText = `${index + 1} / ${assets.length}`
    }
    setImg(mediaViewer.activeFile, mediaViewer.currentIndex)

    const moveLeft = () => {
        const [media, index] = mediaViewer.prevActive()
        setImg(media, index)
    }
    const doRight = () => {
        const [media, index] = mediaViewer.nextActive()
        setImg(media, index)
    }
    const openImg = () => {
        window.open(mediaViewer.activeFile.path, '_blank')
    }

    leftArrow.addEventListener('click', moveLeft)
    rightArrow.addEventListener('click', doRight)
    imageEl.addEventListener('click', openImg)
}

module.exports = {
    setup,
}
