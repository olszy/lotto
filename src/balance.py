#!/usr/bin/env python3
import re
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright, Page
from login import login

# .env loading is handled by login module import


def get_balance(page: Page) -> dict:
    """
    마이페이지에서 예치금 잔액과 구매가능 금액을 조회합니다.
    (오리지널 코드 구조 유지)
    """
    # Navigate to My Page
    # [수정 1] timeout=0 (무제한 대기), wait_until="domcontentloaded" (기본 화면만 뜨면 통과)
    # 원본의 "networkidle"은 깃허브 서버에서 99% 멈춥니다. 이걸 풀어줘야 합니다.
    page.goto("https://www.dhlottery.co.kr/mypage/home", timeout=0, wait_until="domcontentloaded")
    
    # [수정 2] 막연히 기다리는 대신, "총 예치금(#totalAmt)" 숫자가 눈에 보일 때까지만 기다림
    # 이게 없으면 화면 뜨기도 전에 읽으려다 에러 납니다.
    page.wait_for_selector("#totalAmt", state="visible", timeout=30000)
    
    # Get deposit balance (예치금 잔액)
    deposit_el = page.locator("#totalAmt")
    deposit_text = deposit_el.inner_text().strip()
    
    # Get available amount (구매가능)
    available_el = page.locator("#divCrntEntrsAmt")
    available_text = available_el.inner_text().strip()
    
    # Parse amounts (remove non-digits)
    # 혹시 로딩 덜 돼서 빈 값이 와도 에러 안 나게 안전장치(if)만 살짝 추가
    deposit_str = re.sub(r'[^0-9]', '', deposit_text)
    available_str = re.sub(r'[^0-9]', '', available_text)

    deposit_balance = int(deposit_str) if deposit_str else 0
    available_amount = int(available_str) if available_str else 0
    
    return {
        'deposit_balance': deposit_balance,
        'available_amount': available_amount
    }


def run(playwright: Playwright) -> dict:
    """로그인 후 잔액 정보를 조회합니다."""
    # Create browser, context, and page
    # 깃허브 액션 환경에 맞춰 headless=True 유지
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    try:
        # Perform login
        login(page)
        
        # Get balance information
        balance_info = get_balance(page)
        
        # Print results in a clean format
        print(f"💰 예치금 잔액: {balance_info['deposit_balance']:,}원")
        print(f"🛒 구매가능: {balance_info['available_amount']:,}원")
        
        return balance_info
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
