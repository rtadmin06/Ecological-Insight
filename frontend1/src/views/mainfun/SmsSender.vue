<template>
  <div style="width: 100%; height: 100%; padding: 30px; box-sizing: border-box;">
    <div class="sms-container">
      <div class="sms-header">
        <i class="iconfont icon-changjingguanli" style="font-size:28px; margin-right:10px;" />
        <span class="sms-title">短信发件人配置</span>
      </div>

      <el-card class="sms-card" shadow="hover">
        <el-form ref="smsForm" :model="form" :rules="rules" label-width="120px" class="sms-form">
          <el-form-item label="发件人签名" prop="sign">
            <el-input
              v-model="form.sign"
              placeholder="请输入短信签名（如：滨海湿地监测系统）"
              clearable
            />
          </el-form-item>
          <el-form-item label="收信人手机" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="请输入手机号码"
              clearable
            />
          </el-form-item>
          <el-form-item label="短信内容" prop="content">
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="4"
              :maxlength="500"
              show-word-limit
              placeholder="请输入短信内容"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              class="btn-animate btn-animate__shiny"
              :loading="sending"
              @click="submitSend"
            >
              发送短信
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="sms-card" shadow="hover" style="margin-top: 24px;">
        <template #header>
          <span style="font-weight:600;">发送记录</span>
        </template>
        <el-empty v-if="records.length === 0" description="暂无发送记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="(item, idx) in records"
            :key="idx"
            :timestamp="item.time"
            placement="top"
          >
            <el-tag :type="item.success ? 'success' : 'danger'" style="margin-right:8px;">
              {{ item.success ? '成功' : '失败' }}
            </el-tag>
            发送至 {{ item.phone }}：{{ item.content }}
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  name: "SmsSender",
  data() {
    const validatePhone = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入手机号码'))
        return
      }
      if (!/^1[3-9]\d{9}$/.test(value)) {
        callback(new Error('请输入正确的手机号码'))
      } else {
        callback()
      }
    }
    return {
      form: {
        sign: '滨海湿地监测系统',
        phone: '',
        content: '您好，滨海湿地变化监测系统检测到湿地变化，请及时关注。'
      },
      rules: {
        sign: [{ required: true, message: '请输入短信签名', trigger: 'blur' }],
        phone: [{ required: true, validator: validatePhone, trigger: 'blur' }],
        content: [{ required: true, message: '请输入短信内容', trigger: 'blur' }]
      },
      sending: false,
      records: []
    }
  },
  methods: {
    submitSend() {
      this.$refs.smsForm.validate((valid) => {
        if (!valid) return
        this.sending = true
        // 短信发送接口暂未对接，模拟记录
        setTimeout(() => {
          this.records.unshift({
            time: new Date().toLocaleString(),
            phone: this.form.phone,
            content: this.form.content,
            success: false
          })
          this.$message.warning('短信发送功能暂未对接第三方服务，已记录到发送日志。')
          this.sending = false
        }, 800)
      })
    },
    resetForm() {
      this.$refs.smsForm.resetFields()
    }
  }
}
</script>

<style scoped lang="less">
.sms-container {
  max-width: 700px;
  margin: 0 auto;
}
.sms-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}
.sms-title {
  font-size: 22px;
  font-weight: 700;
  font-family: Microsoft JhengHei UI, sans-serif;
  color: var(--theme--color);
}
.sms-card {
  border-radius: 12px;
}
.sms-form {
  padding: 10px 20px;
}
</style>
