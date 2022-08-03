class ImageViewer {
    constructor(assets) {
        this.assets = assets
        this.active = 0
    }
    nextActive() {
        this.active = this.active === (this.assets.length - 1 ) ? 0 : this.active + 1
        return [this.active, this.activeImage]
    }
    prevActive() {
        this.active = this.active === 0 ? this.assets.length - 1 : this.active -1
        return [this.active, this.activeImage]
    }

    get imageIndex() {
        return this.active
    }
    get activeImage() {
        return this.assets[this.active]
    }
}


const setupImgViewer = (resultBody, assets) => {
    const imgViewer = new ImageViewer(assets)
    const leftArrow = resultBody.querySelector('.image-container__nav--left')
    const rightArrow = resultBody.querySelector('.image-container__nav--right')
    const imageName = resultBody.querySelector('.image-name')
    const counter = resultBody.querySelector('.image-overview')
    const imageEl = resultBody.querySelector('img')
    const imageElWrap = resultBody.querySelector('.image__screenshot')
    const videoEl = resultBody.querySelector('source')
    const videoElWrap = resultBody.querySelector('.image__video')

    const setImg = (image, index) => {
        if (image?.format_type === 'image') {
            imageEl.src = image.path

            imageElWrap.classList.remove('hidden')
            videoElWrap.classList.add('hidden')
        } else if (image?.format_type === 'video') {
            videoEl.src = image.path

            videoElWrap.classList.remove('hidden')
            imageElWrap.classList.add('hidden')
        }

        imageName.innerText = image?.name
        counter.innerText = `${index + 1} / ${assets.length}`
    }
    setImg(imgViewer.activeImage, 0)

    const moveLeft = () => {
        const [index, image] = imgViewer.prevActive()
        setImg(image, index)
    }
    const doRight = () => {
        const [index, image] = imgViewer.nextActive()
        setImg(image, index)
    }
    const openImg = () => {
        window.open(imgViewer.activeImage.path, '_blank')
    }

    leftArrow.addEventListener('click', moveLeft)
    rightArrow.addEventListener('click', doRight)
    imageEl.addEventListener('click', openImg)
}

exports.setupImgViewer = setupImgViewer
