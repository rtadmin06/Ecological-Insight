<template>
  
  
  <div ref="imageTofile" style="width: 100%; height: 100%; position: relative;">
    <div id="map" style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;" />
    <el-button
      class="button-dalod btn-animate2 btn-animate__surround"
      type="primary"
      title="变化信息发布"
      @click="toImage()"
    >
    变化信息发布
    </el-button>
    
  
    <el-dialog
      v-model="choose"
      :modal="false"
      title="变化信息发布"
      width="50%"
      top="12%"
    >
      <div class="upload-fun-select">
        <el-radio
          v-model="funtype"
          class="choose-item"
          label="变化检测"
          @change="selectFun"
        >
          滨海湿地变化检测
        </el-radio>
        <el-radio
          v-model="funtype"
          class="choose-item"
          label="目标检测"
          @change="selectFun"
        >
          自然灾害目标检测
        </el-radio>
        
       
      </div>
 
      <el-row>
        <el-button
          type="primary"
          class="btn-animate btn-animate__shiny"
          style="margin: 50px auto"
          @click="goUpload(funtype)"
        >
          查询
        </el-button>
      </el-row>
    </el-dialog>
    <el-dialog
      v-model="isShow"
      :modal="false"
      title="查询结果"
      width="94%"
      top="6%"
    >
      <ImgShow
        :img-arr="imgArr"
      />
      <el-row justify="center">
        <el-button
          type="primary"
          class="btn-animate btn-animate__shiny"
          @click="removeImg"
        >
          确定
        </el-button>
      </el-row>
    </el-dialog>
  </div>
</template>

<script>
import global from "@/global";
import html2canvas from "html2canvas";
import ImgShow from "@/components/ImgShow";
import {historyGetPage} from "@/api/history";
import loadMap from '@/utils/loadMap'

export default {
  name: "Onlinemap",
  components: {  ImgShow },
  data() {
    return {
      isShow: false,
      tmpFile: "",
      choose: false,
      funtype: "变化检测",
      address_detail: null,
      userlocation: { lng: "", lat: "" },
      lng: "",
      lat: "",
      uploadSrc: { list: [], prehandle: 0, denoise: 0, model_path: '' },
      imgArr: [],
    };
  },
  created() {
  },
  mounted() {
  this.initMap()
  },

  methods: {
    historyGetPage,
    loadMap,
    initMap() {
      loadMap(process.env.VUE_APP_BAIDU_MAP_ACCESS_KEY)
          .then(() => {
            // 百度地图API功能
            let myMap = new BMap.Map("map") // 创建Map实例
            myMap.centerAndZoom(new BMap.Point(116.404, 39.915), 19) // 初始化地图,设置中心点坐标和地图级别
            myMap.setMapType(BMAP_HYBRID_MAP);
            //添加地图类型控件
            myMap.addControl(
                new BMap.MapTypeControl({
                  mapTypes: [BMAP_SATELLITE_MAP, BMAP_HYBRID_MAP],
                })
            )
            myMap.setCurrentCity('北京') // 设置地图显示的城市 此项是必须设置的
            myMap.enableScrollWheelZoom(true) //开启鼠标滚轮缩放

            this.$nextTick(function () {
              let th = this;
              let ac = new BMap.Autocomplete({
                //建立一个自动完成的对象
                input: "suggestId",
                location: this.myMap,
              });
              let myValue;
              ac.addEventListener("onconfirm", function (e) {
                //鼠标点击下拉列表后的事件
                let _value = e.item.value;
                myValue =
                    _value.province +
                    _value.city +
                    _value.district +
                    _value.street +
                    _value.business;
                th.address_detail = myValue;
                setPlace();
              });

              function setPlace() {
                myMap.clearOverlays(); //清除地图上所有覆盖物
                function myFun() {
                  th.userlocation = local.getResults().getPoi(0).point; //获取第一个智能搜索的结果
                  myMap.centerAndZoom(th.userlocation, 18);
                  // eslint-disable-next-line no-undef
                  myMap.addOverlay(new BMap.Marker(th.userlocation)); //添加标注
                  th.lng = th.userlocation.lng;
                  th.lat = th.userlocation.lat;
                }

                // eslint-disable-next-line no-undef
                let local = new BMap.LocalSearch(myMap, {
                  //智能搜索
                  onSearchComplete: myFun,
                });
                local.search(myValue)
                //测试输出坐标（指的是输入框最后确定地点的经纬度）
                myMap.addEventListener("click", function () {
                  this.lng = th.userlocation.lng;
                  this.lat = th.userlocation.lat;
                });
              }
            });

          })
          .catch(err => {
            console.log('地图加载失败')
          })
    },
    selectFun() {
      // 选项切换时无需额外操作
    },
    goUpload(type) {
      this.historyGetPage(1, 100, type).then((res) => {
        const list = res.data.data || []
        list.forEach((item) => {
          if (item.before_img && !item.before_img.startsWith('http')) {
            item.before_img = global.BASEURL + item.before_img
          }
          if (item.after_img && !item.after_img.startsWith('http')) {
            item.after_img = global.BASEURL + item.after_img
          }
        })
        this.imgArr = list
        this.choose = false
        if (list.length === 0) {
          this.$message.warning('暂无' + type + '相关记录')
        } else {
          // 等 choose 弹窗关闭动画结束后再打开结果弹窗
          setTimeout(() => {
            this.isShow = true
          }, 300)
        }
      }).catch((err) => {
        console.error(err)
        this.$message.error('查询失败，请检查后端服务是否启动')
      })
    },
    // 页面元素转图片
    toImage() {
      this.choose = true;
      // 手动创建一个 canvas 标签
      const canvas = document.createElement("canvas");
      // 获取父标签，意思是这个标签内的 DOM 元素生成图片
      // imageTofile是给截图范围内的父级元素自定义的ref名称
      let canvasBox = this.$refs.imageTofile;
      // 获取父级的宽高
      const width = parseInt(window.getComputedStyle(canvasBox).width);
      const height = parseInt(window.getComputedStyle(canvasBox).height);
      // 宽高 * 2 并放大 2 倍 是为了防止图片模糊
      canvas.width = width * 2.2;
      canvas.height = height * 2.2;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      const context = canvas.getContext("2d");
      context.scale(2, 2);
      const options = {
        backgroundColor: null,
        canvas: canvas,
        useCORS: true,
      };
      html2canvas(canvasBox, options).then((canvas) => {
        // toDataURL 图片格式转成 base64
        let dataURL = canvas.toDataURL("image/png");
        // this.downloadImage(dataURL)
        this.tmpFile = this.base64toFile(dataURL);
      });
    },
    base64toFile(dataurl) {
      let arr = dataurl.split(",");
      let mime = arr[0].match(/:(.*?);/)[1];
      let suffix = mime.split("/")[1];
      let bstr = atob(arr[1]);
      let n = bstr.length;
      let u8arr = new Uint8Array(n);
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
      }
      return new File([u8arr], `undifined.${suffix}`, {
        type: mime,
      });
    },
    removeImg() {
      this.isShow = false;
    },
  },
};
</script>
<style  scoped lang="less">
.button-dalod {
  position: absolute;
  top: 55vh;
  z-index: 1;
  width: 100px;
}
.input_style {
  font-size: 18px;
  font-weight: 600;
  font-family: Microsoft JhengHei UI, sans-serif;
  margin-bottom: 10px;
}
.choose-item {
  font-size: 25px;
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

}
.img-infor {
  text-align: center;
  font-size: 25px;
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
.upload-fun-select{
  display: flex;
  flex-direction: row;
  justify-content: center;
  flex-wrap: wrap;
}
.model-select{
  margin-top: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>