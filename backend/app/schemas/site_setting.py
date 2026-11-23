from pydantic import BaseModel, Field, ConfigDict


class SiteConfigResponse(BaseModel):
    telegram_url: str = Field("", max_length=512)
    brand_title: str = Field("", max_length=128)
    support_text: str = Field("", max_length=128)
    nav_btn1_text: str = Field("Showcase", max_length=64)
    nav_btn1_link: str = Field("#showcase", max_length=256)
    nav_btn2_text: str = Field("Installation", max_length=64)
    nav_btn2_link: str = Field("#install", max_length=256)
    nav_btn3_text: str = Field("FAQ", max_length=64)
    nav_btn3_link: str = Field("#faq", max_length=256)
    nav_tg_btn_text: str = Field("Join Telegram", max_length=64)
    footer_copy_text: str = Field("", max_length=256)
    # Dynamic Custom Buttons & Visibility
    show_app_details_card: str = Field("true", max_length=16)
    custom_action_btn_text: str = Field("", max_length=128)
    custom_action_btn_link: str = Field("", max_length=512)
    buy_key_btn_text: str = Field("Buy Key Yourself", max_length=128)
    buy_key_btn_link: str = Field("", max_length=512)
    # Master Website Section Controls
    show_top_nav: str = Field("true", max_length=16)
    show_join_tg_btn: str = Field("true", max_length=16)
    join_tg_btn_text: str = Field("JOIN TG", max_length=64)
    show_download_btn: str = Field("true", max_length=16)
    download_btn_text: str = Field("DOWNLOAD APK", max_length=64)
    show_install_guide: str = Field("true", max_length=16)
    show_faq_section: str = Field("true", max_length=16)
    show_footer: str = Field("true", max_length=16)

    model_config = ConfigDict(from_attributes=True)


class SiteConfigUpdate(BaseModel):
    telegram_url: str = Field("", max_length=512)
    brand_title: str = Field("", max_length=128)
    support_text: str = Field("", max_length=128)
    nav_btn1_text: str = Field("Showcase", max_length=64)
    nav_btn1_link: str = Field("#showcase", max_length=256)
    nav_btn2_text: str = Field("Installation", max_length=64)
    nav_btn2_link: str = Field("#install", max_length=256)
    nav_btn3_text: str = Field("FAQ", max_length=64)
    nav_btn3_link: str = Field("#faq", max_length=256)
    nav_tg_btn_text: str = Field("Join Telegram", max_length=64)
    footer_copy_text: str = Field("", max_length=256)
    # Dynamic Custom Buttons & Visibility
    show_app_details_card: str = Field("true", max_length=16)
    custom_action_btn_text: str = Field("", max_length=128)
    custom_action_btn_link: str = Field("", max_length=512)
    buy_key_btn_text: str = Field("Buy Key Yourself", max_length=128)
    buy_key_btn_link: str = Field("", max_length=512)
    # Master Website Section Controls
    show_top_nav: str = Field("true", max_length=16)
    show_join_tg_btn: str = Field("true", max_length=16)
    join_tg_btn_text: str = Field("JOIN TG", max_length=64)
    show_download_btn: str = Field("true", max_length=16)
    download_btn_text: str = Field("DOWNLOAD APK", max_length=64)
    show_install_guide: str = Field("true", max_length=16)
    show_faq_section: str = Field("true", max_length=16)
    show_footer: str = Field("true", max_length=16)

    model_config = ConfigDict(str_strip_whitespace=True)


