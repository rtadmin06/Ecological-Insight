<template>
  <div ref="imageTofile" style="width: 100%; height: 100%; padding: 30px; box-sizing: border-box;">
    <div class="mail-container">
      <div class="mail-header">
        <i class="iconfont icon-changjingguanli" style="font-size:28px; margin-right:10px;" />
        <span class="mail-title">邮件发送人</span>
      </div>

      <el-card class="mail-card" shadow="hover">
        <el-form ref="mailForm" :model="form" :rules="rules" label-width="100px" class="mail-form">
          <el-form-item label="收件人1" prop="receiver1">
            <el-input
              v-model="form.receiver1"
              placeholder="请输入收件人邮箱（必填）"
              clearable
            />
          </el-form-item>
          <el-form-item label="收件人2" prop="receiver2">
            <el-input
              v-model="form.receiver2"
              placeholder="请输入收件人邮箱（可选）"
              clearable
            />
          </el-form-item>
          <el-form-item label="邮件主题" prop="subject">
            <el-input
              v-model="form.subject"
              placeholder="请输入邮件主题"
              clearable
            />
          </el-form-item>
          <el-form-item label="邮件正文" prop="body">
            <el-input
              v-model="form.body"
              type="textarea"
              :rows="4"
              placeholder="请输入邮件正文内容"
            />
          </el-form-item>
          <el-form-item label="附件图片">
            <div class="screenshot-area">
              <div class="attach-btns">
                <el-button
                  type="info"
                  plain
                  :loading="screenshotting"
                  @click="takeScreenshot"
                >
                  {{ screenshotDataUrl ? '重新截图' : '截取当前页面' }}
                </el-button>
                <el-button type="primary" plain @click="$refs.localFileInput.click()">
                  上传本地图片
                </el-button>
                <input
                  ref="localFileInput"
                  type="file"
                  accept="image/*"
                  style="display:none"
                  @change="onLocalFileChange"
                />
                <el-button
                  v-if="screenshotDataUrl"
                  type="danger"
                  plain
                  size="small"
                  @click="screenshotDataUrl = ''"
                >
                  移除附件
                </el-button>
              </div>
              <span v-if="screenshotDataUrl" style="color:#67C23A; font-size:13px;">
                附件已准备好 ✓
              </span>
              <div v-if="screenshotDataUrl" class="screenshot-preview">
                <img :src="screenshotDataUrl" alt="附件预览" />
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              class="btn-animate btn-animate__shiny"
              :loading="sending"
              @click="submitSend"
            >
              发送邮件
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script>
import html2canvas from "html2canvas"
import { sendEmail } from "@/api/mail"

export default {
  name: "MailSender",
  data() {
    const validateEmail = (rule, value, callback) => {
      if (!value) {
        callback()
        return
      }
      const emailReg = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
      if (!emailReg.test(value)) {
        callback(new Error('请输入正确的邮箱格式'))
      } else {
        callback()
      }
    }
    return {
      form: {
        receiver1: '',
        receiver2: '',
        subject: '滨海湿地变化监测 - 变化信息通报',
        body: '您好，请查收附件中的湿地变化检测结果截图。'
      },
      rules: {
        receiver1: [
          { required: true, message: '请输入收件人邮箱', trigger: 'blur' },
          { validator: validateEmail, trigger: 'blur' }
        ],
        receiver2: [
          { validator: validateEmail, trigger: 'blur' }
        ],
        subject: [
          { required: true, message: '请输入邮件主题', trigger: 'blur' }
        ]
      },
      screenshotDataUrl: '',
      screenshotting: false,
      sending: false
    }
  },
  methods: {
    async takeScreenshot() {
      this.screenshotting = true
      try {
        const canvas = await html2canvas(document.body, {
          useCORS: true,
          backgroundColor: '#fff',
          scale: 1.5
        })
        this.screenshotDataUrl = canvas.toDataURL("image/png")
        this.$message.success("截图成功")
      } catch (e) {
        this.$message.error("截图失败：" + e.message)
      } finally {
        this.screenshotting = false
      }
    },
    submitSend() {
      this.$refs.mailForm.validate(async (valid) => {
        if (!valid) return
        const toList = [this.form.receiver1]
        if (this.form.receiver2) toList.push(this.form.receiver2)

        this.sending = true
        try {
          await sendEmail({
            to: toList,
            subject: this.form.subject,
            body: this.form.body,
            image: this.screenshotDataUrl || null
          })
          this.$message.success("邮件发送成功！")
          this.screenshotDataUrl = ''
        } finally {
          this.sending = false
        }
      })
    },
    onLocalFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = (evt) => {
        this.screenshotDataUrl = evt.target.result
        this.$message.success('图片已加载')
      }
      reader.readAsDataURL(file)
      // 清空 input，允许重复选同一文件
      e.target.value = ''
    },
    resetForm() {
      this.$refs.mailForm.resetFields()
      this.screenshotDataUrl = ''
    }
  }
}
</script>

<style scoped lang="less">
.mail-container {
  max-width: 700px;
  margin: 0 auto;
}
.mail-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}
.mail-title {
  font-size: 22px;
  font-weight: 700;
  font-family: Microsoft JhengHei UI, sans-serif;
  color: var(--theme--color);
}
.mail-card {
  border-radius: 12px;
}
.mail-form {
  padding: 10px 20px;
}
.screenshot-area {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}
.attach-btns {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.screenshot-preview {
  margin-top: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  max-width: 400px;
  img {
    width: 100%;
    display: block;
  }
}
</style>
