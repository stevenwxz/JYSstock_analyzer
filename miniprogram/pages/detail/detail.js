// pages/detail/detail.js
const app = getApp()

Page({
  data: {
    stock: null,
    stockCode: '',
    loading: false
  },

  onLoad(options) {
    const stockCode = options.code
    if (stockCode) {
      this.setData({
        stockCode: stockCode
      })
      this.loadStockDetail(stockCode)
    }
  },

  /**
   * 加载股票详情
   */
  loadStockDetail(code) {
    this.setData({
      loading: true
    })

    app.request({
      url: `/stocks/detail/${code}`,
      success: (data) => {
        this.setData({
          stock: data,
          loading: false
        })

        // 更新页面标题
        wx.setNavigationBarTitle({
          title: `${data.name} - 详情`
        })
      },
      fail: () => {
        this.setData({
          loading: false
        })
      }
    })
  },

  /**
   * 刷新数据
   */
  onRefresh() {
    if (this.data.stockCode) {
      this.loadStockDetail(this.data.stockCode)
    }
  }
})
