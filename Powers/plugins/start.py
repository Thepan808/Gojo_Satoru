import os
from random import choice
from time import gmtime, strftime, time

from pyrogram import enums, filters
from pyrogram.enums import ChatMemberStatus as CMS
from pyrogram.enums import ChatType
from pyrogram.errors import (MediaCaptionTooLong, MessageNotModified,
                             QueryIdInvalid, UserIsBlocked)
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from Powers import (HELP_COMMANDS, LOGGER, PYROGRAM_VERSION, PYTHON_VERSION,
                    UPTIME, VERSION)
from Powers.bot_class import Gojo
from Powers.utils.custom_filters import command
from Powers.utils.extras import StartPic
from Powers.utils.kbhelpers import ikb
from Powers.utils.start_utils import (gen_cmds_kb, gen_start_kb, get_help_msg,
                                      get_private_note, get_private_rules)
from Powers.vars import Config


@Gojo.on_message(
    command("donate") & (filters.group | filters.private),
)
async def donate(_, m: Message):
    cpt = """
Hey Obrigado por seu pensamento de me doar!
Quando você doa, todo o fundo vai para o meu desenvolvimento, que faz com que seja rápido e responsivo.
Sua doação também pode me dar um novo recurso ou dois, que eu não consegui devido a limitações do servidor.

Todo o fundo seria colocado em meus serviços, como banco de dados, armazenamento e hospedagem!

Você pode doar através desse link: [Link para doação](https://www.donationalerts.com/r/the_panda_official)
     """

    LOGGER.info(f"{m.from_user.id} fetched donation text in {m.chat.id}")
    await m.reply_photo(photo=str(choice(StartPic)), caption=cpt)
    return


@Gojo.on_callback_query(filters.regex("^close_admin$"))
async def close_admin_callback(_, q: CallbackQuery):
    user_id = q.from_user.id
    user_status = (await q.message.chat.get_member(user_id)).status
    if user_status not in {CMS.OWNER, CMS.ADMINISTRATOR}:
        await q.answer(
            "Você nem é um administrador, não tente essa merda!",
            show_alert=True,
        )
        return
    if user_status != CMS.OWNER:
        await q.answer(
            "Você é apenas um administrador, não proprietário\nFique dentro dos seus limites!",
            show_alert=True,
        )
        return
    await q.message.edit_text("Fechado!")
    await q.answer("Menu fechado!", show_alert=True)
    return


@Gojo.on_message(
    command("start") & (filters.group | filters.private),
)
async def start(c: Gojo, m: Message):

    if m.chat.type == ChatType.PRIVATE:
        if len(m.text.strip().split()) > 1:
            help_option = (m.text.split(None, 1)[1]).lower()

            if help_option.startswith("note") and (
                help_option not in ("note", "notes")
            ):
                await get_private_note(c, m, help_option)
                return
    
            if help_option.startswith("rules"):
                LOGGER.info(f"{m.from_user.id} fetched privaterules in {m.chat.id}")
                await get_private_rules(c, m, help_option)
                return

            help_msg, help_kb = await get_help_msg(m, help_option)

            if not help_msg:
                return
            elif help_msg:
                await m.reply_photo(
                    photo=str(choice(StartPic)),
                    caption=help_msg,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    reply_markup=help_kb,
                    quote=True,
                )
                return
            if len(help_option.split("_",1)) == 2:
                if help_option.split("_")[1] == "help":
                    await m.reply_photo(
                        photo=str(choice(StartPic)),
                        caption=help_msg,
                        parse_mode=enums.ParseMode.MARKDOWN,
                        reply_markup=help_kb,
                        quote=True,
                    )
                    return
                
        try:
            cpt = f"""
Hey [{m.from_user.first_name}](http://t.me/{m.from_user.username})! Eu sou Savage ✨.
Estou aqui para ajudá-lo a gerenciar seu grupo(s)!
Pressione /help para saber mais sobre como me usar em todo o meu potencial!

Junte-se ao meu [Canal](https://t.me/botssaved) para obter informações sobre todas as atualizações mais recentes."""

            await m.reply_photo(
                photo=str(choice(StartPic)),
                caption=cpt,
                reply_markup=(await gen_start_kb(m)),
                quote=True,
            )
        except UserIsBlocked:
            LOGGER.warning(f"Bot bloqueado por {m.from_user.id}")
    else:
      kb = InlineKeyboardMarkup(
        [
          [
            InlineKeyboardButton(
              "Conecte-me ao dm", 
              url=f"https://{Config.BOT_USERNAME}.t.me/",
            ),
          ],
        ],
      )
        
      await m.reply_photo(
        photo=str(choice(StartPic)),
        caption="Estou vivo :3",
        reply_markup=kb,
        quote=True,
      )
    return


@Gojo.on_callback_query(filters.regex("^start_back$"))
async def start_back(_, q: CallbackQuery):
    try:
        cpt = f"""
Ei [{q.from_user.first_name}](http://t.me/{q.from_user.username})! Eu sou Savage ✨.
Estou aqui para ajudá-lo a gerenciar seu grupo(s)!
Pressione /help para saber mais sobre como me usar em todo o meu potencial!

Junte-se ao meu [Canal](http://t.me/botssaved) para obter informações sobre todas as atualizações mais recentes."""

        await q.edit_message_caption(
            caption=cpt,
            reply_markup=(await gen_start_kb(q.message)),
        )
    except MessageNotModified:
        pass
    await q.answer()
    return


@Gojo.on_callback_query(filters.regex("^commands$"))
async def commands_menu(_, q: CallbackQuery):
    ou = await gen_cmds_kb(q.message)
    keyboard = ikb(ou, True)
    try:
        cpt = f"""
Ei **[{q.from_user.first_name}](http://t.me/{q.from_user.username})**! Eu sou Savage✨.
Estou aqui para ajudá-lo a gerenciar seu grupo(s)!
Comandos disponíveis:
× /start: Iniciar o bot
× /help: Dê-lhe esta mensagem.

Você pode usar `$` e `!` no lugar de `/` como seu comando de prefixo
"""

        await q.edit_message_caption(
            caption=cpt,
            reply_markup=keyboard,
        )
    except MessageNotModified:
        pass
    except QueryIdInvalid:
        await q.message.reply_photo(
            photo=str(choice(StartPic)), caption=cpt, reply_markup=keyboard
        )

    await q.answer()
    return


@Gojo.on_message(command("help"))
async def help_menu(_, m: Message):
    if len(m.text.split()) >= 2:
        textt = m.text.replace(" ","_",).replace("_"," ",1)
        help_option = (textt.split(None)[1]).lower()
        help_msg, help_kb = await get_help_msg(m, help_option)

        if not help_msg:
            LOGGER.error(f"No help_msg found for help_option - {help_option}!!")
            return

        LOGGER.info(
            f"{m.from_user.id} fetched help for '{help_option}' text in {m.chat.id}",
        )

        if m.chat.type == ChatType.PRIVATE:
            if len(help_msg) >= 1026:
                await m.reply_text(
                    help_msg, parse_mode=enums.ParseMode.MARKDOWN, quote=True
                )
            await m.reply_photo(
                photo=str(choice(StartPic)),
                caption=help_msg,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=help_kb,
                quote=True,
            )
        else:

            await m.reply_photo(
                photo=str(choice(StartPic)),
                caption=f"Pressione o botão abaixo para obter ajuda para <i>{help_option}</i>",
                reply_markup=InlineKeyboardMarkup(
                  [
                    [
                      InlineKeyboardButton(
                        "Help",
                        url=f"t.me/{Config.BOT_USERNAME}?start={help_option}",
                        ),
                    ],
                  ],
                ),
            )
    else:

        if m.chat.type == ChatType.PRIVATE:
            ou = await gen_cmds_kb(m)
            keyboard = ikb(ou, True)
            msg = f"""
Ei **[{m.from_user.first_name}](http://t.me/{m.from_user.username})**!Eu sou Savage✨.
Estou aqui para ajudá-lo a gerenciar seu grupo(s)!
Comandos disponíveis:
× /start: Iniciar o bot
× /help: Dê-lhe esta mensagem."""
        else:
            keyboard = InlineKeyboardMarkup(
              [
                [
                  InlineKeyboardButton(
                    "Help", 
                    url=f"t.me/{Config.BOT_USERNAME}?start=start_help",
                  ),
                ],
              ],
            )
            msg = "Entre em contato comigo na Dm para obter a lista de comandos possíveis."

        await m.reply_photo(
            photo=str(choice(StartPic)),
            caption=msg,
            reply_markup=keyboard,
        )

    return

@Gojo.on_callback_query(filters.regex("^bot_curr_info$"))
async def give_curr_info(c: Gojo, q: CallbackQuery):
    start = time()
    up = strftime("%Hh %Mm %Ss", gmtime(time() - UPTIME))
    x = await c.send_message(q.message.chat.id, "Pinging..")
    delta_ping = time() - start
    await x.delete()
    txt = f"""
🏓 Ping : {delta_ping * 1000:.3f} ms
📈 Ativo : {up}
🤖 Versão do Bot: {VERSION}
🐍 Versão do Python: {PYTHON_VERSION}
🔥 Versão do pyrogram: {PYROGRAM_VERSION}
    """
    await q.answer(txt, show_alert=True)
    return

@Gojo.on_callback_query(filters.regex("^plugins."))
async def get_module_info(c: Gojo, q: CallbackQuery):
    module = q.data.split(".", 1)[1]

    help_msg = HELP_COMMANDS[f"plugins.{module}"]["help_msg"]

    help_kb = HELP_COMMANDS[f"plugins.{module}"]["buttons"]
    try:
      await q.edit_message_caption(
          caption=help_msg,
          parse_mode=enums.ParseMode.MARKDOWN,
          reply_markup=ikb(help_kb, True, todo="commands"),
      )
    except MediaCaptionTooLong:
      await c.send_message(chat_id=q.message.chat.id,text=help_msg,)
    await q.answer()
    return
