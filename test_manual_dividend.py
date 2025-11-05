from config.dividend_override import get_manual_dividend_yield

print('中国人保(601319)手动配置的股息率:', get_manual_dividend_yield('601319'))
print('中国太保(601601)手动配置的股息率:', get_manual_dividend_yield('601601'))
print('中国铝业(601600)手动配置的股息率:', get_manual_dividend_yield('601600'))