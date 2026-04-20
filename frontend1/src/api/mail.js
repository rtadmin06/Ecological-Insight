import { request } from "@/api/request.js"

/**
 * 发送邮件
 * @param {Object} data - { to: string[], subject: string, body: string, image: string }
 */
export function sendEmail(data) {
    return request({
        method: 'POST',
        url: '/api/mail/send',
        data
    })
}
