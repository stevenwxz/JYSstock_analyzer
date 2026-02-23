// pages/index/index.js
const app = getApp()

Page({
  data: {
    stocks: [],
    marketSummary: null,
    loading: false,
    updateTime: '',
    isHistory: false  // 是否是历史记录模式
  },

  onLoad(options) {
    // 检查是否是查看历史记录
    if (options && options.isHistory && options.filename) {
      this.setData({ isHistory: true })
      this.loadHistoryDetail(options.filename)
    } else {
      this.loadRecommendedStocks()
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadRecommendedStocks(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载推荐股票
   */
  loadRecommendedStocks(callback) {
    this.setData({
      loading: true
    })

    app.request({
      url: '/stocks/recommend',
      success: (data) => {
        const now = new Date()
        const timeStr = `${now.getMonth() + 1}月${now.getDate()}日 ${this.formatTime(now.getHours())}:${this.formatTime(now.getMinutes())}`

        // 处理股票数据,将评级转换为CSS类名
        const stocks = (data.stocks || []).map(stock => {
          return {
            ...stock,
            gradeClass: this.formatGradeClass(stock.grade)
          }
        })

        this.setData({
          stocks: stocks,
          marketSummary: data.marketSummary || null,
          loading: false,
          updateTime: timeStr
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
   * 点击股票跳转详情
   */
  onStockTap(e) {
    const stockCode = e.currentTarget.dataset.code
    wx.navigateTo({
      url: `/pages/detail/detail?code=${stockCode}`
    })
  },

  /**
   * 格式化评级为CSS类名
   * A+ -> grade-a-plus
   * B+ -> grade-b-plus
   */
  formatGradeClass(grade) {
    if (!grade) return 'grade-c'

    const gradeMap = {
      'A+': 'grade-a-plus',
      'A': 'grade-a',
      'B+': 'grade-b-plus',
      'B': 'grade-b',
      'C': 'grade-c',
      'D': 'grade-d'
    }

    return gradeMap[grade] || 'grade-c'
  },

  /**
   * 加载历史详情
   */
  loadHistoryDetail(filename) {
    this.setData({
      loading: true
    })

    app.request({
      url: `/analysis/detail/${filename}`,
      success: (data) => {
        // 处理股票数据,将评级转换为CSS类名
        const stocks = (data.stocks || []).map(stock => {
          return {
            ...stock,
            gradeClass: this.formatGradeClass(stock.grade)
          }
        })

        // 格式化日期时间
        const analysisDate = data.analysisDate || ''
        const analysisTime = data.analysisTime || ''
        const timeStr = analysisDate ? `${analysisDate} ${analysisTime}` : ''

        this.setData({
          stocks: stocks,
          marketSummary: data.marketSummary || null,
          loading: false,
          updateTime: timeStr
        })

        // 更新页面标题
        wx.setNavigationBarTitle({
          title: `历史分析 - ${analysisDate}`
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
   * 格式化时间
   */
  formatTime(num) {
    return num < 10 ? '0' + num : num
  }
})
