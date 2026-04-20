
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
      请上传包含<span class="go-bold">图片的文件夹</span><i
        class="iconfont icon-wenjianjia"
      />或者<span
        class="go-bold"
      >图片</span><i
        class="iconfont icon-tupiantianjia"
      />
    </p>
    <p style="text-decoration: underline">
      
    </p><p>
      
    </p>
    <el-card style="border: 4px dashed var(--el-border-color);position: relative">
      <div
        v-if="fileList1.length||fileList2.length"
        class="clear-queue"
      >
        <el-button
          type="primary"
          class="btn-animate2 btn-animate__surround"
          @click="clearQueue"
        >
          清空图片
        </el-button>
      </div>
      <div class="upload-box">
        <div class="upload-item">
          <el-upload
            ref="uploadA"
            v-model:file-list="fileList1"
            drag
            action="#"
            multiple
            :auto-upload="false"
            @change="checkFile1"
          >
            <i class="iconfont icon-yunduanshangchuan" />
            <div class="el-upload__text">
              将文件夹或图片拖到此处，或<em>点击上传</em>
            </div>
            <div
              class="el-upload__tip"
            >
              只能上传一张或多张图片，请在下方上传文件夹
            </div>
          </el-upload>
          <div>
            <input
              id="upload-fileA"
              ref="refFileA"
              type="file"
              webkitdirectory
              directory
              multiple
              @change="uploadFirst"
            >
            <i
              class="iconfont icon-wenjianshangchuan"
              @click="file1Click"
            >上传文件夹</i>
          </div>
        </div>
        <div class="upload-item">
          <el-upload
            ref="uploadB"
            v-model:file-list="fileList2"
            drag
            action="#"
            multiple
            :auto-upload="false"
            @change="checkFile2"
          >
            <i class="iconfont icon-yunduanshangchuan" />
            <div class="el-upload__text">
              将文件夹或图片拖到此处，或<em>点击上传</em>
            </div>
            <div
              class="el-upload__tip"
            >
              只能上传一张或多张图片，请在下方上传文件夹
            </div>
          </el-upload>
          <div>
            <input
              id="upload-fileB"
              ref="refFileB"
              type="file"
              webkitdirectory
              directory
              multiple
              @change="uploadSecond"
            >
            <i
              class="iconfont icon-wenjianshangchuan"
              @click="file2Click"
            >上传文件夹</i>
          </div>
        </div>
      </div>
     
      <el-row
        justify="center"
        align="middle"
      >
      
        <i
          class="iconfont icon-tuxingtuxiangchuli"
        />
        
        <p>图像复原：</p>
        <p>
          <label class="prehandle-label container">
            <input
              ref="histogram"
              type="checkbox"
              @change="selectHistogram()"
            >
            <span class="checkmark" />
            <span class="go-bold label-words">去雾</span>
          </label>
        </p>
        <p>
          <label class="container prehandle-label">
            <input
              ref="sharpen"
              type="checkbox"
              @change="selectSharpen()"
            >
            <span class="checkmark" />
            <span class="go-bold label-words">去模糊</span>
          </label>
        </p>

      
      </el-row>
      <el-row
        justify="center"
        align="middle"
      >
        
      </el-row>
      
      <el-row justify="center">
        
      </el-row>

      <div class="handle-button">
        <el-button
          type="primary"
          class=" btn-animate btn-animate__shiny"
          :loading="loadButton"
          @click="startProcess"
        >
          开始处理
        </el-button>
      </div>

      <el-divider v-if="!upload.prehandle" />
      <div v-if="upload.prehandle">
       
       
      </div>
    </el-card>

    <Tabinfor>
      <template #left>
        <div
          id="sub-title"
          style="font-size: 25px"
        >
          结果图<i
            class="iconfont icon-dianji"
          />
        </div>
      </template>
    </Tabinfor>
    <el-divider />
    <Tabinfor>
      <template #left>
        <p>
          对输出的结果图进行<span class="go-bold">展示</span><i
            class="iconfont icon-xuanran"
          />
          <span class="go-bold">，点击图片</span>即可预览
          
        </p>
      </template>
      <template #mid>
        
        <label
          v-if="resultArr.length!==0"
          class="prehandle-label container"
        >
          <input
            ref="hole"
            type="checkbox"
            :checked="resultArr[currentIndex].is_hole"
            @click="toggleHoleStatus"
          >
         
         
        </label>
        
      </template>
      <template #right>
        <p>
          <span class="go-bold"><i
            class="iconfont icon-shuaxin"
            style=" padding-right: 55px;"
            @click="getMore"
          ><span class="hidden-sm-and-down" @click="success">信息上传</span></i></span>
        </p>
      </template>
    </Tabinfor>

    <el-card class="render-box">
      <div
        class="render-img-box"
      >
        <div
          v-if="preMode===1"
          class="display-modeA"
        >
          <div
            id="image-slider"
            @mousemove="sliderMouseMove"
            @mousedown="sliderMouseDown"
            @mouseup="sliderMouseUp"
            @mouseleave="sliderMouseLeave"
          >
            <div v-show="!isHiddenMask">
              <img
                v-if="resultArr[currentIndex]?.data.mask && !holeShow"
                :src="resultArr[currentIndex].data.mask "
                alt="mask"
                class="mask-img"
              >
              <img
                v-if="resultArr[currentIndex]?.data.mask_hole && holeShow"
                :src="resultArr[currentIndex].data.mask_hole "
                alt="mask"
                class="mask-img"
              >
              <img
                v-if="!resultArr[currentIndex]?.data.mask"
                :src="exampleArr[0].data.mask "
                alt="mask"
                class="mask-img"
              >
            </div>
            <img
              v-if="resultArr[currentIndex]?.before_img"
              :src="resultArr[currentIndex].before_img "
              alt=""
            >
            <img
              v-if="!resultArr[currentIndex]?.before_img"
              :src="exampleArr[0].before_img "
              alt=""
            >
            <div class="img-wrapper">
              <img
                v-if="resultArr[currentIndex]?.before_img1"
                :src="resultArr[currentIndex].before_img1"
                alt=""
              >
              <img
                v-if="!resultArr[currentIndex]?.before_img1"
                :src="exampleArr[0].before_img1"
                alt=""
              >
            </div>
            <div class="handle">
              <div class="handle-line" />
              <div class="handle-circle">
                &#171;&#187;
              </div>
              <div class="handle-line" />
            </div>
          </div>
        </div>

        <div
          v-if="preMode===2 "
          class="display-modeB"
        >
          <div class="render-img modeB-item">
            <p class="handle-words">
              T0时期
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before_img"
              :preview-src-list="[resultArr[currentIndex].before_img]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before_img"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before_img"
              :preview-src-list="[exampleArr[0].before_img]"
              :preview-teleported="true"
              :src="exampleArr[0].before_img"
              fit="cover"
            />
          </div>
    
          <div class="render-img modeB-item">
            <p class="handle-words">
              T1时期
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before_img1"
              :preview-src-list="[resultArr[currentIndex].before_img1]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before_img1"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before_img1"
              :preview-src-list="[exampleArr[0].before_img1]"
              :preview-teleported="true"
              :src="exampleArr[0].before_img1"
              fit="cover"
            />
          </div>

          <div class="render-img modeB-item">
            <p class="handle-words">
              输出变化图
            </p>
            <div style="position: relative">
              <transition
                enter-active-class="animate__animated animate__bounceIn"
                leave-active-class="animate__animated animate__hinge"
              >
                <div v-if="!holeShow">
                  <el-image
                    v-if="onRenderResult && !holeShow"
                    :preview-src-list="[onRenderResult]"
                    :preview-teleported="true"
                    :src="onRenderResult"
                    fit="cover"
                    style="width: 100%"
                  />
                </div>
              </transition>
              <transition
                enter-active-class="animate__animated animate__bounceIn"
                leave-active-class="animate__animated animate__hinge"
              >
                <div
                  v-if="holeShow"
                  style="position: absolute;top: 0;right: 0;"
                >
                  <el-image
                    v-if="onRenderResult && holeShow"
                    :preview-src-list="[onRenderResult]"
                    :preview-teleported="true"
                    :src="onRenderResult"
                    fit="cover"
                    style="width: 100%"
                  />
                </div>
              </transition>
            </div>
            
            <el-image
              v-if="!onRenderResult"
              :preview-src-list="[onRenderExample]"
              :preview-teleported="true"
              :src="onRenderExample"
              fit="cover"
              style="width: 100%"
            />  
        </div>

        
        <div class="render-img modeB-item">
            <p class="handle-words">
              变化级别图
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before"
              :preview-src-list="[resultArr[currentIndex].beforeg]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before"
              :preview-src-list="[exampleArr[0].before]"
              :preview-teleported="true"
              :src="exampleArr[0].before"
              fit="cover"
            />
          </div>
    
          <div class="render-img modeB-item">
            <p class="handle-words">
              整体区域变化级别
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before1"
              :preview-src-list="[resultArr[currentIndex].before1]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before1"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before1"
              :preview-src-list="[exampleArr[0].before1]"
              :preview-teleported="true"
              :src="exampleArr[0].before1"
              fit="cover"
            />
          </div>

          <div class="render-img modeB-item">
            <p class="handle-words">
              局部区域变化级别
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before2"
              :preview-src-list="[resultArr[currentIndex].before2]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before2"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before2"
              :preview-src-list="[exampleArr[0].before2]"
              :preview-teleported="true"
              :src="exampleArr[0].before2"
              fit="cover"
            />
          </div>

          <div class="render-img modeB-item">
            <p class="handle-words">
            
            </p>
            <el-image
              v-if="resultArr[currentIndex]?.before3"
              :preview-src-list="[resultArr[currentIndex].before3]"
              :preview-teleported="true"
              :src="resultArr[currentIndex].before3"
              fit="cover"
            />
            <el-image
              v-if="!resultArr[currentIndex]?.before3"
              :preview-src-list="[exampleArr[0].before3]"
              :preview-teleported="true"
              :src="exampleArr[0].before3"
              fit="cover"
            />
          </div>

       

       
        </div>
        
        
      </div>

      <div class="swiper-img">
        <div
          v-for="(item, index) in 5"
          :key="index"
          class="img-box"
        >
          <el-image
            v-if="resultArr[currentQroup+index]?.after_img"
            :src="holeShow ? resultArr[currentQroup+index]?.data.hole : resultArr[currentQroup+index]?.after_img"
            :class="{'render-border':onRender===index}"
            @click="goRenderThis(index)"
          />
        </div>
      </div>

      <div 
        v-show="!dragShow"
        class="drag-control hidden-md-and-down"
        @click="dragShow=true"
      >
        <i
          class="iconfont icon-cebianshouqi"
        />
      </div>
    </el-card>
    <Bottominfor />
  </div>
</template>


<script>
import {
  createSrc,
  imgUpload,
  histogramUpload,
  getCustomModel
} from "@/api/upload";
import {
  downloadimgWithWords,
  getImgArrayBuffer,
  atchDownload,
} from "@/utils/download.js";
import { historyGetPage } from "@/api/history";
import Tabinfor from "@/components/Tabinfor";
import Bottominfor from "@/components/Bottominfor";
import DraggableItem from "@/components/DraggableItem";
import global from "@/global";
export default {
  name: "Detectchanges",
  components: {
    Tabinfor,
    Bottominfor,
    DraggableItem
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      document.querySelector(".el-main").scrollTop = 0;
    });
  },
  
  data() {
    return {
      loadButton: false,
      holeShow:true,
      isSliderLocked: false,
      preMode: 2,
      pairs: [],
      hisPairs: [],
      shaPairs: [],
      canUpload: true,
      onRender: 0,
      isUpload: true,
      hisNum: 0,
      value:null,
      renderstyle: "原图",
      funtype: "变化检测",
      scrollTop: "",

      currentQroup: 0,
      currentIndex: 0,

      fileList1: [],
      fileList2: [],

      uploadSrc1: [],
      uploadSrc2: [],
      uploadSrc: [],
      upload: {
        window_size:256,
        stride:128,
        list: [
          {
            first: "",
            second: "",
          },
        ],
        
        prehandle: 0,
        denoise: 0,
        model_path:''
        
      },
      modelPathArr:[],
      //直方图处理
      uploadSrc3: [],
      uploadSrc4: [],
      histogramSrc: [],
      myhistogram: {
        list: [
          {
            first: "",
            second: "",
          },
        ],
        prehandle: 0,
      },
      Img1: [],
      Img2: [],
      Img3: [],

      //锐化处理
      sharpenSrc1: [],
      sharpenSrc2: [],
      sharpenSrc: [],
      mysharpen: {
        list: [
          {
            first: "",
            second: "",
          },
        ],
        prehandle: 0,
      },
      sharpenImg1: [],
      sharpenImg2: [],

      preHandle: {
        list: [
          {
            first: "",
            second: "",
          },
        ],
      },

      hole: {
        id: "",
      },
      resultArr:[],
      devidedArr:[],
      onRenderResult:'',
      exampleArr:[{
          before_img : require("@/assets/image/example/7_1.png"),
          before : require("@/assets/image/example/7.png"),
          before_img1: require("@/assets/image/example/7_2.png"),
          before1 : require("@/assets/image/example/1_1.png"),
          before2 : require("@/assets/image/example/1_2.png"),
          before3 : require("@/assets/image/example/x1.png"),
          after_img:require('@/assets/image/example/7.png'),
          data:{
              0:require('@/assets/image/example/flash.png'),
              1:require('@/assets/image/example/aurora.png'),
              2:require('@/assets/image/example/woods.png'),
              3:require('@/assets/image/example/neon.png'),
            mask:require('@/assets/image/example/mask.png')
          }
      }],
      onRenderExample:require('@/assets/image/example/7.png'),
      
      isHiddenMask:false,
      dragShow:true,
      sizeValue:[0,200]
    };
  },
  created() {
    this.getMore();
    this.getCustomModel('change_detection').then((res)=>{
      this.modelPathArr = res.data.data
      this.upload.model_path = this.modelPathArr[0]?.model_path
    }).catch((rej)=>{})
  },

  methods: {
    downloadimgWithWords,
    historyGetPage,
    imgUpload,
    getCustomModel,
    createSrc,
    getImgArrayBuffer,
    atchDownload,
    histogramUpload,
    startProcess(){
      this.loadButton= true
      const that = this
      setTimeout(function () {
        that.$message.success("处理成功")
        that.loadButton= false
      },2000 )
    },
    success(){
      this.getMore()
      this.$message.success("刷新成功！");
    },
    clearQueue() {
      this.fileList1 = [];
      this.fileList2 = [];
      this.$message.success("清除成功");
    },
    goRenderThis(index) {
      this.currentIndex = this.currentQroup;
      this.currentIndex += index;
      this.onRender = index;
      this.setOneWay(this.renderstyle)
    },
    goRenderThese(index) {
      this.currentQroup = 5 * index;
      this.currentIndex = 5 * index;
      this.goRenderThis(0);
    },
    setOneWay(style,isShowExample,holeStyle) {
      this.renderstyle = style;
      if(isShowExample){
        switch (style){
          case '原图': this.onRenderExample = this.exampleArr[0].after_img;break
          case '森林': this.onRenderExample = this.exampleArr[0].data[2];break
          case '霓虹': this.onRenderExample = this.exampleArr[0].data[3];break
          case '闪电': this.onRenderExample = this.exampleArr[0].data[0];break
          case '极光': this.onRenderExample = this.exampleArr[0].data[1];break
        }
        return
      }
      if(!holeStyle){
        switch (style){
          case '原图': this.onRenderResult = this.resultArr[this.currentIndex].after_img;break
          case '森林': this.onRenderResult = this.resultArr[this.currentIndex].data[2];break
          case '霓虹': this.onRenderResult = this.resultArr[this.currentIndex].data[3];break
          case '闪电': this.onRenderResult = this.resultArr[this.currentIndex].data[0];break
          case '极光': this.onRenderResult = this.resultArr[this.currentIndex].data[1];break
        }
      }else{
        switch (style){
          case '原图': this.onRenderResult = this.resultArr[this.currentIndex].data.hole;break
          case '森林': this.onRenderResult = this.resultArr[this.currentIndex].data.hole_style[2];break
          case '霓虹': this.onRenderResult = this.resultArr[this.currentIndex].data.hole_style[3];break
          case '闪电': this.onRenderResult = this.resultArr[this.currentIndex].data.hole_style[0];break
          case '极光': this.onRenderResult = this.resultArr[this.currentIndex].data.hole_style[1];break
        }
      }

    },
    uploadfile() {
      this.uploadSrc = [];
      if(this.upload.window_size===this.upload.stride){
        this.$message.error('窗口大小不能等于步长')
        return
      }
      if (
          this.fileList1.length !== this.fileList2.length ||
          this.fileList1.length === 0
      ) {
        this.$message.error("请按照要求上传文件夹或图片！");
      } else {
        let formData1 = new FormData();
        let formData2 = new FormData();
        for (const item of this.fileList1) {
          formData1.append("files", item) ||
          formData1.append("files", item.raw);
          formData1.append("type", "变化检测");
        }
        for (const item of this.fileList2) {
          formData2.append("files", item) ||
          formData2.append("files", item.raw);
          formData2.append("type", "变化检测");
        }
        let upload1 = new Promise((resolve, reject) => {
            this.createSrc(formData1).then((res) => {
              this.uploadSrc1 = res.data.data;
              resolve();
            }).catch((rej)=>{})
        });
        let upload2 = new Promise((resolve, reject) => {
          this.createSrc(formData2).then((res) => {
            this.uploadSrc2 = res.data.data;
            resolve();
          }).catch((rej)=>{})
        });
        Promise.all([upload1, upload2])
            .then((val) => {
              this.uploadSrc = this.uploadSrc1.concat(this.uploadSrc2);
              this.uploadSrc = this.uploadSrc.map((item) => {
                return {
                  filename: item.filename.substring(
                      item.filename.indexOf("/") + 1,
                      item.length
                  ),
                  src: item.src,
                };
              });

              this.pairs = this.uploadSrc.map((item) => {
                return item.filename.substring(
                    item.filename.indexOf("/") + 1,
                    item.length
                );
              });

              this.checkPairs(this.pairs);
              if (!this.canUpload) {
                this.$message.error(
                    "检测到命名对应失败的图片，请检查您的文件命名"
                );
              } else {
                this.upload.list = this.getList(this.uploadSrc);
                this.imgUpload(this.upload,'change_detection')
                    .then((res) => {
                      this.$refs.uploadA.clearFiles();
                      this.$refs.uploadB.clearFiles();
                      this.fileList1 = [];
                      this.fileList2 = [];
                      this.$message.success("上传成功");
                      this.isUpload = true;
                      this.getMore();
                      if (this.upload.list.length >= 10) {
                        this.$confirm(
                            "上传图片过多，是否压缩?",
                            "提示",
                            {
                              confirmButtonText: "确定",
                              cancelButtonText: "取消",
                              type: "warning",
                            }
                        )
                            .then(() => {
                              this.goCompress(this.upload.list.length);
                            })
                            .catch(() => {});
                      }
                    })
                    .catch((rej) => {});
              }
            })
            .catch((rej) => {});
      }
    },
    getList(beforeData) {
      //算法参考
      //https://blog.csdn.net/weixin_45575273/article/details/108321137?utm_medium=distribute.pc_aggpage_search_result.none-task-blog-2~aggregatepage~first_rank_ecpm_v1~rank_v31_ecpm-3-108321137-null-null.pc_agg_new_rank&utm_term=%E6%95%B0%E7%BB%84%E4%B8%AD%E7%9A%84%E5%AF%B9%E8%B1%A1id%E7%9B%B8%E5%90%8C%E7%9A%84%E5%AF%B9%E8%B1%A1%E7%BB%84%E6%88%90%E4%B8%80%E4%B8%AA%E6%96%B0%E6%95%B0%E7%BB%84&spm=1000.2123.3001.4430
      let tempArr = [];
      let afterData = [];
      for (let i = 0; i < beforeData.length; i++) {
        if (tempArr.indexOf(beforeData[i].filename) === -1) {
          afterData.push(beforeData[i]);
          tempArr.push(beforeData[i].filename);
        } else {
          for (let j = 0; j < afterData.length; j++) {
            Reflect.deleteProperty(afterData[j], "photo_id");
            // Reflect.deleteProperty(afterData[j], "filename");
            afterData[j].first = afterData[j].src;
            afterData[j].second = beforeData[i + j].src;
            // Reflect.deleteProperty(afterData[j], "src");
          }
          break;
        }
      }
      return  afterData;
    },
    goCompress(num) {
      this.$message.success("正在下载压缩");
      this.historyGetPage(1, num, "变化检测").then((res) => {
        this.atchDownload(
            res.data.data.map((item) => {
              return { after_img: item.after_img, id: item.id };
            })
        );
      }).catch((rej)=>{})
    },
    getMore() {
      this.historyGetPage(1, 20, "变化检测")
          .then((res) => {
            const prefix = global.BASEURL
            const ts = '?t=' + Date.now()
            const addBase = (v) => {
              if (!v) return ''
              const url = String(v).startsWith('http') ? v : prefix + v
              return url + ts
            }
            res.data.data.forEach((item)=>{
              item['before_img1'] = addBase(item.before_img1)
              item['before_img']  = addBase(item.before_img)
              item['before1']     = addBase(item.before1)
              item['before']      = addBase(item.before)
              item['before2']     = addBase(item.before2)
              item['before3']     = addBase(item.before3)
              item['after_img']   = addBase(item.after_img)
              item.data['hole']   = addBase(item.data['hole'])
              item.data['hole_style'][0] = addBase(item.data['hole_style'][0])
              item.data['hole_style'][1] = addBase(item.data['hole_style'][1])
              item.data['hole_style'][2] = addBase(item.data['hole_style'][2])
              item.data['hole_style'][3] = addBase(item.data['hole_style'][3])
              item.data[0] = addBase(item.data[0])
              item.data[1] = addBase(item.data[1])
              item.data[2] = addBase(item.data[2])
              item.data[3] = addBase(item.data[3])
              item.data['mask']      = addBase(item.data.mask)
              item.data['mask_hole'] = addBase(item.data.mask_hole)
            })
            this.resultArr = []
            this.$nextTick(() => {
              this.resultArr = res.data.data
              this.currentIndex = 0
              this.currentQroup = 0
              this.onRender = 0
              if (this.resultArr.length > 0) {
                this.onRenderResult = this.resultArr[0].after_img
              }
            })
          })
          .catch((rej) => {});
    },
    selectHistogram() {
      if (this.$refs.histogram.checked === true) {
        if (
            this.fileList1.length !== this.fileList2.length ||
            this.fileList1.length === 0
        ) {
          if (this.upload.prehandle === 1) {
            this.$refs.histogram.checked = false;
            this.upload.prehandle = 0;
          } else {
            this.$refs.histogram.checked = false;
            this.$message.error("请先按要求上传图片");
          }
        } else {
          this.upload.prehandle = 1;
          this.myhistogram.prehandle = 1;
          this.$message.success("去雾处理完成");
          if (this.$refs.sharpen.checked === true) {
            this.$refs.sharpen.checked = false;
          }
          let formData1 = new FormData();
          let formData2 = new FormData();

          for (const item of this.fileList1) {
            formData1.append("files", item) ||
            formData1.append("files", item.raw);
            formData1.append("type", "变化检测");
          }

          for (const item of this.fileList2) {
            formData2.append("files", item) ||
            formData2.append("files", item.raw);
            formData2.append("type", "变化检测");
          }
          let upload3 = new Promise((resolve, reject) => {
            this.createSrc(formData1).then((res) => {
              this.uploadSrc3 = res.data.data.splice(0, 3);
              this.Img1 = this.uploadSrc3.map((item) => {
                return global.BASEURL + item.src;
              });
              resolve();
            }).catch((rej)=>{})
          });
          let upload4 = new Promise((resolve, reject) => {
            this.createSrc(formData2).then((res) => {
              this.uploadSrc4 = res.data.data.splice(0, 3);
              this.Img3 = this.uploadSrc4.map((item) => {
                return global.BASEURL + item.src;
              });
              resolve();
            }).catch((rej)=>{})
          });
          Promise.all([upload3, upload4]).then((val) => {
            this.histogramSrc = this.uploadSrc3.concat(this.uploadSrc4);
            //https://blog.csdn.net/qq_27342239/article/details/118078113去除“/”前的字符
            this.histogramSrc = this.histogramSrc.map((item) => {
              return {
                filename: item.filename.substring(
                    item.filename.indexOf("/") + 1,
                    item.length
                ),
                src: item.src,
              };
            });

            this.hisPairs = this.histogramSrc.map((item) => {
              return item.filename.substring(
                  item.filename.indexOf("/") + 1,
                  item.length
              );
            });

            this.checkPairs(this.hisPairs);

            if (!this.canUpload) {
              this.$message.error(
                  "检测到命名对应失败的图片，请检查您的文件命名"
              );
              this.Img1 = [];
              this.Img3 = [];
            } else {
              this.myhistogram.list = this.getList(this.histogramSrc);
              this.histogramUpload(this.myhistogram).then((res) => {
                this.Img2 = res.data.data.map((item) => {
                  return global.BASEURL + item;
                });
                this.Img2 = this.Img2.splice(0, 3);
              }).catch((rej)=>{})
            }
          }).catch((rej)=>{})
        }
      } else {
        this.$message.success("取消直方图处理");
        this.upload.prehandle = 0;
        this.myhistogram.prehandle = 0;
      }
    },
    selectSharpen() {
      if (
          this.fileList1.length !== this.fileList2.length ||
          this.fileList1.length === 0
      ) {
        if (this.upload.prehandle === 4) {
          this.$refs.sharpen.checked = false;
          this.upload.prehandle = 0;
        } else {
          this.$refs.sharpen.checked = false;
          this.$message.error("请先按要求上传图片");
        }
      } else {
        if (this.$refs.histogram.checked === true) {
          this.$refs.histogram.checked = false;
        }

        if (this.$refs.sharpen.checked === false) {
          this.myhistogram.prehandle = 0;
          this.$message.success("取消处理");
          this.upload.prehandle = 0;
        } else {
          this.$message.success("去模糊处理完成");
          this.upload.prehandle = 4;
          this.mysharpen.prehandle = 4;
          let formData1 = new FormData();
          let formData2 = new FormData();

          for (const item of this.fileList1) {
            formData1.append("files", item) ||
            formData1.append("files", item.raw);
            formData1.append("type", "变化检测");
          }

          for (const item of this.fileList2) {
            formData2.append("files", item) ||
            formData2.append("files", item.raw);
            formData2.append("type", "变化检测");
          }
          let upload1 = new Promise((resolve, reject) => {
            this.createSrc(formData1).then((res) => {
              this.sharpenSrc1 = res.data.data.splice(0, 3);
              this.Img1 = this.sharpenSrc1.map((item) => {
                return global.BASEURL + item.src;
              });
              resolve();
            }).catch((rej)=>{})
          });
          let upload2 = new Promise((resolve, reject) => {
            this.createSrc(formData2).then((res) => {
              this.sharpenSrc2 = res.data.data.splice(0, 3);
              this.Img3 = this.sharpenSrc2.map((item) => {
                return global.BASEURL + item.src;
              });
              resolve();
            }).catch((rej)=>{})
          });
          Promise.all([upload1, upload2]).then((val) => {
            this.sharpenSrc = this.sharpenSrc1.concat(this.sharpenSrc2);
            this.sharpenSrc = this.sharpenSrc.map((item) => {
              return {
                filename: item.filename.substring(
                    item.filename.indexOf("/") + 1,
                    item.length
                ),
                src: item.src,
              };
            });
            this.shaPairs = this.sharpenSrc.map((item) => {
              return item.filename.substring(
                  item.filename.indexOf("/") + 1,
                  item.length
              );
            });

            this.checkPairs(this.hisPairs);

            if (!this.canUpload) {
              this.$message.error(
                  "检测到命名对应失败的图片，请检查您的文件命名"
              );
              this.Img1 = [];
              this.Img3 = [];
            } else {
              this.mysharpen.list =  this.getList(this.sharpenSrc);
              this.histogramUpload(this.mysharpen).then((res) => {
                this.sharpenImg1 = res.data.data.map((item) => {
                  return global.BASEURL + item.first;
                });

                this.sharpenImg2 = res.data.data.map((item) => {
                  return global.BASEURL + item.second;
                });
              });
            }
          }).catch((rej)=>{})
        }
      }
    },

    selectFilter() {
      if (this.$refs.smooth.checked === true) {
        this.$refs.smooth.checked = false;
      }
      if (this.$refs.filter.checked === false) {
        this.$message.success("取消高斯滤波处理");
        this.upload.denoise = 0;
      } else {
        this.$message.success("高斯滤波处理");
        this.upload.denoise = 5;
      }
    },
    selectSmooth() {
      if (this.$refs.filter.checked === true) {
        this.$refs.filter.checked = false;
      }
      if (this.$refs.smooth.checked === false) {
        this.$message.success("取消平滑处理");
        this.upload.denoise = 0;
      } else {
        this.$message.success("平滑处理");
        this.upload.denoise = 3;
      }
    },
    toggleHoleStatus() {
      this.resultArr[this.currentIndex].is_hole = !this.resultArr[this.currentIndex].is_hole
      this.holeShow = !this.holeShow
      this.setOneWay(this.renderstyle,this.resultArr.length===0,this.holeShow)
    },
    uploadFirst() {
      this.checkFile1(...this.$refs.refFileA.files);
      if (this.canUpload) {
        this.fileList1.push(...this.$refs.refFileA.files);
      } else {
        setTimeout(() => {
          this.$message.error("检测到您上传的文件夹内存在不符合规范的图片类型");
        }, 1000);
      }
    },
    uploadSecond() {
      this.checkFile2(...this.$refs.refFileB.files);
      if (this.canUpload) {
        this.fileList2.push(...this.$refs.refFileB.files);
      } else {
        setTimeout(() => {
          this.$message.error("检测到您上传的文件夹内存在不符合规范的图片类型");
        }, 1000);
      }
    },
    file1Click() {
      document.querySelector("#upload-fileA").click();
    },
    file2Click() {
      document.querySelector("#upload-fileB").click();
    },
    checkFile1(file) {
      const whiteList = ["jpg", "jpeg", "png", "JPG", "JPEG"];
      const fileSuffix = file.name.substring(file.name.lastIndexOf(".") + 1);
      if (whiteList.indexOf(fileSuffix) === -1) {
        this.$message.error("只允许上传jpg, jpeg, png, JPG, 或JPEG格式,请重新上传");
        this.fileList1 = [];
        this.canUpload = false;
      } else {
        this.canUpload = true;
      }
    },
    checkFile2(file) {
      const whiteList = ["jpg", "jpeg", "png", "JPG", "JPEG"];
      const fileSuffix = file.name.substring(file.name.lastIndexOf(".") + 1);
      if (whiteList.indexOf(fileSuffix) === -1) {
        this.$message.error("只允许上传jpg, jpeg, png, JPG, 或JPEG格式,请重新上传");
        this.fileList2 = [];
        this.canUpload = false;
      } else {
        this.canUpload = true;
      }
    },
    checkPairs(list) {
      let s = list.join(",") + ",";
      let j = 0;
      for (let i = 0; i < list.length; i++) {
        if (s.replace(list[i] + ",", "").indexOf(list[i] + ",") > -1) {
        } else {
          j++;
          break;
        }
      }
      this.canUpload = j === 0;
    },
    changePreMode() {
      if (this.preMode === 1) {
        this.preMode = 2;
      } else {
        this.preMode = 1;
      }
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

      handle.style.left = `calc(${((mouseX / sliderWidth) * 100).toFixed(
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
    vanishDrag(){
      this.dragShow = false
    },
    hideMask(){
      this.isHiddenMask = !this.isHiddenMask
    }
  },
};
</script>

<style scoped lang="less">
* {
  font-family: SimHei sans-serif;
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
  background: var(--theme--color);
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
#sub-title{
  font-size: 25px;
}
#sub-title:hover:after {
  left: 0;
  right: 0;
  width: 220px;
}
.render-box {
  .render-img {
    // width: 100%;
    max-height: 600px;
    overflow: hidden;

  }
  .render-style {
    height: auto;
  }
}
.cl-checkbox {
  display: block;
  height: auto;
  text-align: center;
}

.style-title {
  text-align: center;
  font-size: 22px;
  font-family: "幼圆", sans-serif;
  font-weight: 600;
  margin-bottom: 20px;
}
.img-index {
  text-align: center;
  height: 428px;
  align-content: center;
  line-height: 428px;
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
}
.clear-queue {
  left: 0;
  position: absolute;
  top: 20%;
  z-index: 100;
}
.render-border {
  border: var(--theme--color) 0.5rem solid;
}
.mask-img{
  position: absolute;
  top: 0;
  z-index:2
}
#image-slider {
  position: relative;
  max-width:100%;
  max-height: 100%;
  overflow: hidden;
  border-radius: 1em;
  cursor: col-resize;
  display: inline-block;
}

#image-slider img {
  display: block;
  height: 100%;
  max-width:650px;
  max-height: 650px;
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
  z-index: 3;
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

@media (max-width: 768px) {
  :root {
    --image-slider-width: 90vw;
  }
}
.el-row{
  position: inherit;
}
.style-words {
  line-height: 30px;
  height: 30px;
  transition: all 0.4s;
  margin-bottom: 10px;
  cursor: pointer;
  font-size: 18px;
}
.style-words:hover {
  color: white;
}
.normal:hover {
  background-color: var(--theme--color);
}
.woods:hover {
  background-image: linear-gradient(#9be15d, #00e3ae 100%);
}
.neon:hover {
  background-image: linear-gradient(135deg, #f761a1 15%, #8c1bab 100%);
}
.flash:hover {
  background-image: linear-gradient(135deg, #c2ffd8 10%, #465efb 100%);
}
.aurora:hover {
  background-image: linear-gradient(#011142, #00bbc9 100%);
}
.active-normal {
  background-color: rgb(64, 158, 255);
}
.active-woods {
  background-image: linear-gradient(#9be15d, #00e3ae 100%);
}
.active-neon {
  background-image: linear-gradient(135deg, #f761a1 15%, #8c1bab 100%);
}
.active-flash {
  background-image: linear-gradient(135deg, #c2ffd8 10%, #465efb 100%);
}
.active-aurora {
  background-image: linear-gradient(#011142, #00bbc9 100%);
}
.el-radio /deep/{
  height: 62px;
}
.folder-row{
  display: flex;
  flex-direction: row;
  justify-content: space-evenly;
}
.upload-box{
  display: flex;
  flex-direction:row;
  justify-content: space-evenly;
  flex-wrap: wrap;
}
.render-img-box{
  display: flex;
  justify-content: space-evenly;
  flex-wrap: wrap;
  flex-direction: row;
  .display-modeB{
    display: flex;
    flex-wrap: wrap ;
    flex-direction: row;
    justify-content: center;
    width: 80%;
    .modeB-item{
      margin: 10px;
      width:25%;
    }
  }
  .render-select-box{
    width: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
  }
}

.render-select{
  display: flex;
  flex-direction: column;
}
.drag-control{
  position: absolute;
  right: 20px;
  top: 400px;
  width: 33px;
  height: 20px;
  text-align: center;
  padding: 5px;
  color: var(--theme--color);
  background: rgb(237, 242, 245);
  border-radius: 0.2rem;
  .iconfont {
    display: block;
    &:hover{
      background-color: rgb(228, 235, 240);
    }
  }
}
.slider-box{
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  .slider-item{
    margin: 10px;
    width: 450px;
  }
}

</style>