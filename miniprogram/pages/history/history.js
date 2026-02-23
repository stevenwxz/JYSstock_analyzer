// pages/history/history.js
const app = getApp()

Page({
  data: {
    historyList: [],
    loading: false
  },

  onLoad() {
    this.loadHistory()
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadHistory(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载历史记录
   */
  loadHistory(callback) {
    this.setData({
      loading: true
    })

    app.request({
      url: '/analysis/history?days=30',
      success: (data) => {
        this.setData({
          historyList: data || [],
          loading: false
        })
        callback && callback()
      },
      fail: () => {
        this.setData({
          loading: false
        })
        callback && callback()
      }
    })
  },

  /**
   * 点击历史记录查看详情
   */
  onHistoryTap(e) {
    const filename = e.currentTarget.dataset.filename
    if (filename) {
      // 跳转到首页,并传递filename参数
      wx.navigateTo({
        url: `/pages/index/index?filename=${filename}&isHistory=true`
      })
    }
  }
})
