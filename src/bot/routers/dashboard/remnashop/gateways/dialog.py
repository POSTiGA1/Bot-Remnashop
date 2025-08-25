from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, ListGroup, Row, Select, Start, SwitchTo
from magic_filter import F

from src.bot.routers.extra.test import show_dev_popup
from src.bot.states import DashboardRemnashop, RemnashopGateways
from src.bot.widgets import Banner, I18nFormat, IgnoreUpdate
from src.core.enums import BannerName, Currency

from .getters import currency_getter, gateway_getter, gateways_getter
from .handlers import (
    on_active_toggle,
    on_default_currency_selected,
    on_gateway_selected,
    on_gateway_test,
    on_merchant_input,
    on_secret_input,
)

gateways = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-gateways-main"),
    ListGroup(
        Row(
            Button(
                text=I18nFormat("btn-gateway-title", type=F["item"]["type"]),
                id="select_gateway",
                on_click=on_gateway_selected,
            ),
            Button(
                text=I18nFormat("btn-gateway-test"),
                id="test_gateway",
                # on_click=on_gateway_test,
                on_click=show_dev_popup,
            ),
            Button(
                text=I18nFormat("btn-gateway-active", is_active=F["item"]["is_active"]),
                id="active_toggle",
                on_click=on_active_toggle,
            ),
        ),
        id="gateways_list",
        item_id_getter=lambda item: item["id"],
        items="gateways",
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-gateways-default-currency"),
            id="default_currency",
            state=RemnashopGateways.CURRENCY,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardRemnashop.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    IgnoreUpdate(),
    state=RemnashopGateways.MAIN,
    getter=gateways_getter,
)

gateway_merchant = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-gateways-merchant", type=F["type"]),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnashopGateways.MAIN,
        ),
    ),
    MessageInput(func=on_merchant_input),
    IgnoreUpdate(),
    state=RemnashopGateways.MERCHANT,
    getter=gateway_getter,
)

gateway_secret = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-gateways-secret", type=F["type"]),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnashopGateways.MERCHANT,
        ),
    ),
    MessageInput(func=on_secret_input),
    IgnoreUpdate(),
    state=RemnashopGateways.SECRET,
    getter=gateway_getter,
)

default_currency = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-gateways-default-currency"),
    Column(
        Select(
            text=I18nFormat(
                "btn-gateways-default-currency-choice",
                symbol=F["item"]["symbol"],
                currency=F["item"]["currency"],
                enabled=F["item"]["enabled"],
            ),
            id="currency",
            item_id_getter=lambda item: item["currency"],
            items="currency_list",
            type_factory=Currency,
            on_click=on_default_currency_selected,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnashopGateways.MAIN,
        ),
    ),
    IgnoreUpdate(),
    state=RemnashopGateways.CURRENCY,
    getter=currency_getter,
)

router = Dialog(
    gateways,
    gateway_merchant,
    gateway_secret,
    default_currency,
)
