// app.js
App({
  globalData: {
    // API服务器地址 - 开发环境
    // 开发者工具调试: http://localhost:5000/api
    // 真机调试: 使用电脑局域网IP
    // 生产环境: 修改为实际服务器HTTPS地址
    apiBaseUrl: 'http://192.168.0.36:5000/api',

    // 用户信息
    userInfo: null
  },

  onLaunch() {
    console.log('小程序启动')

    // 检查小程序更新
    this.checkUpdate()
  },

  /**
   * 检查小程序更新
   */
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager()

      updateManager.onCheckForUpdate((res) => {
        if (res.hasUpdate) {
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好,是否重启应用?',
              success(res) {
                if (res.confirm) {
                  updateManager.applyUpdate()
                }
              }
            })
          })

          updateManager.onUpdateFailed(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本下载失败',
              showCancel: false
            })
          })
        }
      })
    }
  },

  /**
   * 全局HTTP请求封装
   */
  request(options) {
    const { url, method = 'GET', data = {}, success, fail } = options

    wx.showLoading({
      title: '加载中...',
      mask: true
    })

    wx.request({
      url: this.globalData.apiBaseUrl + url,
      method: method,
      data: data,
      header: {
        'content-type': 'application/json'
      },
      success: (res) => {
        wx.hideLoading()

        if (res.statusCode === 200 && res.data.code === 200) {
          success && success(res.data.data)
        } else {
          wx.showToast({
            title: res.data.message || '请求失败',
            icon: 'none',
            duration: 2000
          })
          fail && fail(res.data)
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '网络错误',
          icon: 'none',
          duration: 2000
        })
        fail && fail(err)
      }
    })
  }
})
