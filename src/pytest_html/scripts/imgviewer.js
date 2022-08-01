class ImageViewer {
    constructor(assets) {
        this.assets = assets
        this.active = 0
    }
    nextActive () {
        this.active = this.active === (this.assets.length - 1 ) ? 0 : this.active + 1
        return [this.active, this.activeImage]
    }
    prevActive () {
        this.active = this.active === 0 ? this.assets.length - 1 : this.active -1 
        return [this.active, this.activeImage]
    }
    
    get imageIndex () {
        return this.active
    }
    get activeImage () {
        return this.assets[this.active]
    }
}


const setupImgViewer = (resultBody, assets) => {
    const imgViewer = new ImageViewer(assets)
    
    const leftArrow = resultBody.querySelector('.image-container__nav--left')
    const rightArrow = resultBody.querySelector('.image-container__nav--right')
    const imgContainer = resultBody.querySelector('.image-container__frame')
    const imageName = resultBody.querySelector('.image-name')
    const counter = resultBody.querySelector('.image-overview')
    
    const imgel = document.createElement('img')
    imgContainer.appendChild(imgel)

    const setImg = (image, index) => {
        imgel.src = image?.path
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
        window.open(imgViewer.activeImage, '_blank')
    }

    leftArrow.addEventListener('click', moveLeft)
    rightArrow.addEventListener('click', doRight)
    imgel.addEventListener('click', openImg)
}

exports.setupImgViewer = setupImgViewer