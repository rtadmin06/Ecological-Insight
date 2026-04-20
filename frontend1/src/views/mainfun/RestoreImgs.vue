<template>
  <div>
    <Tabinfor>
      <template #left>
        <div
          id="sub-title"
        >
          湿地变化监测系统<i
            class="iconfont icon-dianji"
          />
        </div>
      </template>
    </Tabinfor>
    <el-divider />
    <p>
      请手动设置阈值<span class="go-bold"></span>
        
    </p>
    <el-row
      type="flex"
      justify="center"
    >
      <el-col :span="24">
        <el-card style="border: 4px dashed var(--el-border-color)">
          <div
            v-if="fileList.length"
            class="clear-queue"
          >
            <el-button
              type="primary"
              class="btn-animate2 btn-animate__surround"
              @click="clearQueue"
            >
              
            </el-button>
          </div>
          <el-upload
            ref="upload"
            v-model:file-list="fileList"
            class="upload-card"
            drag
            action="#"
            multiple
            :auto-upload="false"
            @change="beforeUpload(fileList[fileList.length - 1].raw)"
          >
            <i class="iconfont icon-yunduanshangchuan" />
            <el-input v-model="form.name" placeholder="请输入阈值" style="width: 80%"></el-input>

            
            <div
              class="el-upload__tip"
            >
            
            </div>
          </el-upload>
          <el-row justify="center">
            <input
              id="folder"
              ref="uploadFile"
              type="file"
              webkitdirectory
              directory
              multiple
              @change="uploadMore()"
            >
            
          </el-row>

          <el-row justify="center">
            <p>
             
            </p>
          </el-row>
         
          <div class="handle-button">
            <el-button
              type="primary"
              class="btn-animate btn-animate__shiny"
              @click="upload('图像复原','image_restoration')"
            >
              确定
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-divider />
    
    

    
    <Bottominfor />
  </div>
</template>
<script>
import {createSrc,imgUpload,getCustomModel} from "@/api/upload";
import {historyGetPage} from "@/api/history";
import {getUploadImg, goCompress, upload} from "@/utils/getUploadImg";
import {atchDownload, downloadimgWithWords, getImgArrayBuffer} from "@/utils/download.js";
import Tabinfor from "@/components/Tabinfor";
import Bottominfor from "@/components/Bottominfor";
import MyVueCropper from "@/components/MyVueCropper";

export default {
  name: "Restoreimgs",
  components: {
    Tabinfor,
    Bottominfor,
    MyVueCropper,
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      document.querySelector(".el-main").scrollTop = 0;
    });
  },
  data() {
    return {
      canUpload:true,
      fileimg: "",
      file: {},
      isNotCut: true,
      cutVisible: false,
      funtype: "图像复原",
      scrollTop: "",
      fit: "fill",
      fileList: [],
      uploadSrc: {
        list: [],
        model_path:''
      },
      modelPathArr:[],
      isSliderLocked: false,
      onRender: 0,
      currentIndex:0,
      currentQroup:0,
      imgArr:[],
      isUpload:false,
      form: {
          name: '',
          region: '',
          date1: '',
          date2: '',
          delivery: false,
          type: [],
          resource: '',
          desc: ''
        }
    };
  },
  watch:{
    uploadSrc:{
      handler(newVal,oldVal){
        this.uploadSrc = newVal
      },
      deep:true,
      immediate:true
    },
    isUpload:{
      handler(newVal, oldVal) {
        this.isUpload = newVal
      }
    }
  },
  created() {
    this.getUploadImg("图像复原")
    this.getCustomModel('image_restoration').then((res)=>{
      this.modelPathArr = res.data.data
      this.uploadSrc.model_path = this.modelPathArr[0]?.model_path
    }).catch((rej)=>{})
  },
  methods: {
    imgUpload,
    getCustomModel,
    historyGetPage,
    createSrc,
    getUploadImg,
    upload,
    downloadimgWithWords,
    getImgArrayBuffer,
    atchDownload,
    goCompress,
    onSubmit() {
        console.log('submit!');
      },
    clearQueue() {
      this.fileList = [];
      this.$message.success("清除成功");
    },
    notvisible() {
      this.cutVisible = false;
      this.fileList = [];
    },
    getMore() {
      this.getUploadImg("图像复原");
      this.goShowThese(0)
      console.log(this.imgArr.length)
    },
    uploadMore() {
      this.beforeUpload(...this.$refs.uploadFile.files)
      if(this.canUpload){
        this.fileList.push(...this.$refs.uploadFile.files);
      }else{
        setTimeout(() => {
          this.$message.error('检测到您上传的文件夹内存在不符合规范的图片类型')
        }, 1000);
      }
    },
    fileClick() {
      document.querySelector("#folder").click();
    },
    beforeUpload(file) {
      this.cutVisible = this.$refs.cut.checked;
      const fileSuffix = file.name.substring(file.name.lastIndexOf(".") + 1)
      const whiteList = ['jpg','jpeg','png','JPG','JPEG']
      if (whiteList.indexOf(fileSuffix) === -1) {
        this.$message.error("只允许上传jpg, jpeg, png, JPG, 或JPEG格式,请重新上传");
        this.fileList= []
        this.canUpload = false
        this.cutVisible = false;
      }
      else{
        this.canUpload = true
        this.fileimg = window.URL.createObjectURL(new Blob([file]));
      }
    },
    select() {
      this.isNotCut = this.$refs.cut.checked;
    },
    goShowThis(index) {
      this.currentIndex = this.currentQroup;
      this.currentIndex += index;
      this.onRender = index
    },
    goShowThese(index) {
      this.currentQroup = 5 * index;
      this.currentIndex = 5 * index;
      this.goShowThis(0)
    },
    sliderMouseMove(event) {
      const slider = document.querySelector("#image-slider");
      const wrapper = document.querySelector(".img-wrapper");
      const handle = document.querySelector(".handle");

      if (this.isSliderLocked) return;

      const sliderLeftX = slider.offsetLeft;

      const sliderWidth = slider.clientWidth;

      const sliderHandleWidth = handle.clientWidth;

      let mouseX = event.clientX - sliderLeftX;

      if (mouseX < 0) mouseX = 0;
      else if (mouseX > sliderWidth) mouseX = sliderWidth;

      wrapper.style.width = `${((1 - mouseX / sliderWidth) * 100).toFixed(4)}%`;

      handle.style.left = `calc(${((mouseX/ sliderWidth) * 100).toFixed(
          4
      )}% - ${sliderHandleWidth / 2}px)`;

    },
    sliderMouseDown() {
      if (this.isSliderLocked) this.isSliderLocked = false;
      this.sliderMouseMove(event);
    },
    sliderMouseUp() {
      if (!this.isSliderLocked) this.isSliderLocked = true;
    },
    sliderMouseLeave() {
      if (this.isSliderLocked) this.isSliderLocked = true;
    },
  },
}
</script>

<style lang="less" scoped>
* {
  font-family: SimHei sans-serif;
}
#sub-title{
  font-size: 25px;
}
#sub-title:hover:after {
  left: 0%;
  right: 0%;
  width: 220px;
}
.clear-queue {
  position: relative;
  left: -20px;
  top: 14%;
  z-index: 100;
}
.img-index {
  align-items: center;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  flex-wrap: wrap;
}
.index-number {
  font-family: Yu Gothic Medium;
  font-style: oblique;
  font-size: 30px;
  margin-left: 5px;
  margin-right: 10px;
}
.img-infor {
  text-align: center;
  font-size: 18px;
  margin-top: 5px;
  margin-bottom: 10px;
  width: 256px;
  height: 30px;
  font-weight: 500;
  font-family: Microsoft JhengHei UI, sans-serif;
}
.custom-pic{
  width: 256px;
  height: 256px;
}

#image-slider {
  position: relative;
  max-width:600px;
  overflow: hidden;
  border-radius: 1em;
  cursor: col-resize;
  display: inline-block;
}

#image-slider img {
  display: block;
  width:580px;
  height:580px;
  object-fit: cover;
  pointer-events: none;
  user-select: none;
}

#image-slider .img-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: 50%;
  overflow: hidden;
  z-index: 1;
}

#image-slider .img-wrapper img {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
}

#image-slider .handle {
  border: 0 solid red;
  position: absolute;
  top: 0;
  left: calc(50% - var(--image-slider-handle-width) / 2);
  width: var(--image-slider-handle-width);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  user-select: none;
  z-index: 2;
}

#image-slider .handle-circle {

  color: white;
  border: 2px solid white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: space-evenly;
}

#image-slider .handle-line {
  width: 2px;
  flex-grow: 1;
  background: white;
}

//.el-row{
//  position: inherit;
//  //获取滑窗容器的左偏移量
//}
.restore-img{
  display: flex;
  flex-direction: row;
  justify-content: space-around;
  flex-wrap: wrap;
}
.style-title {
  text-align: center;
  font-size: 22px;
  font-family: "幼圆", sans-serif;
  font-weight: 600;
  margin-bottom: 20px;
}
.list {
  text-align: center;
  cursor: pointer;
  width: auto;
  height: 20px;
  background-color: rgb(236, 244, 255);
  position: relative;
  margin-bottom: 10px;
}
.list-number:hover::after {
  width: 100%;
  background: rgb(64, 158, 255);
}
.list-number::after {
  position: absolute;
  content: "";
  width: 0;
  height: 100%;
  top: 0;
  left: 0;
  border-radius: 2px 2px 0 0;
  transition: 0.4s;
  z-index: -1;
}
.list:hover * {
  color: #ecf4ff !important;
}
.list-number {
  z-index: 1;
}
.list-number {
  overflow: hidden;
  margin: 0 auto;
  width: auto;
  height: 20px;
  position: relative !important;
  border-radius: 2px !important;
}

.swiper-img {
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  width: 100%;
  margin-top: 30px;
  .img-box {
    flex: 1;
    height: 100%;
    overflow: hidden;
    opacity: 0.7;
    transition: all 0.6s;
    margin-right: 10px;
    justify-content: space-between;
  }
}
.render-border {
  border: var(--theme--color) 0.5rem solid;
}
.el-radio /deep/{
  height: 62px;
}
.restore-img-box{
  display: flex;
  justify-content: space-evenly;
  flex-wrap: wrap;
  flex-direction: row;
  .choose-restore{
    width: 250px;
    display: flex;
    flex-wrap: wrap;
    flex-direction: column;
    justify-content:center;
  }
}
</style>