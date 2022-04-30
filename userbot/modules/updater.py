"""
This module updates the userbot based on upstream revision
"""

import sys
from os import environ, execle, remove

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from userbot import CMD_HANDLER as cmd
from userbot import CMD_HELP, HEROKU_API_KEY, HEROKU_APP_NAME, UPSTREAM_REPO_URL
from userbot.events import register
from userbot.utils import edit_delete, edit_or_reply, zed_cmd


async def gen_chlog(repo, diff):
    d_form = "%d/%m/%y"
    return "".join(
        f"• [{c.committed_datetime.strftime(d_form)}]: {c.summary} <{c.author}>\n"
        for c in repo.iter_commits(diff)
    )


async def print_changelogs(zz, ac_br, changelog):
    changelog_str = (
        f"𓆰 𝗦𝗢𝗨𝗥𝗖𝗘 𝙕𝞝𝘿 - 𝑼𝑷𝑫𝑨𝑻𝑬 𝑴𝑺𝑮 𓆪\n **𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**\n** ⪼ يوجـد تحـديث جديد لسورس زدثـون ༗.**\n\n**- الملفـات المحدثـه :**\n`{changelog}`"
    )
    if len(changelog_str) > 4096:
        await edit_or_reply(zz, "**Changelog terlalu besar, dikirim sebagai file.**")
        with open("output.txt", "w+") as file:
            file.write(changelog_str)
        await zz.client.send_file(zz.chat_id, "output.txt")
        remove("output.txt")
    else:
        await zz.client.send_message(zz.chat_id, changelog_str)
    return True


async def deploy(zz, repo, ups_rem, ac_br, txt):
    if HEROKU_API_KEY is not None:
        import heroku3

        heroku = heroku3.from_key(HEROKU_API_KEY)
        heroku_app = None
        heroku_applications = heroku.apps()
        if HEROKU_APP_NAME is None:
            await edit_or_reply(
                zz,
                "**[HEROKU]: Harap Tambahkan Variabel** `HEROKU_APP_NAME` "
                " **untuk deploy perubahan terbaru dari Userbot.**",
            )
            repo.__del__()
            return
        for app in heroku_applications:
            if app.name == HEROKU_APP_NAME:
                heroku_app = app
                break
        if heroku_app is None:
            await edit_or_reply(
                zz,
                f"{txt}\n"
                "**Kredensial Heroku tidak valid untuk deploy Zee-Userbot dyno.**",
            )
            return repo.__del__()
        try:
            from userbot.modules.sql_helper.globals import addgvar, delgvar

            delgvar("restartstatus")
            addgvar("restartstatus", f"{zz.chat_id}\n{zz.id}")
        except AttributeError:
            pass
        ups_rem.fetch(ac_br)
        repo.git.reset("--hard", "FETCH_HEAD")
        heroku_git_url = heroku_app.git_url.replace(
            "https://", "https://api:" + HEROKU_API_KEY + "@"
        )
        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
            remote.set_url(heroku_git_url)
        else:
            remote = repo.create_remote("heroku", heroku_git_url)
        try:
            remote.push(refspec="HEAD:refs/heads/master", force=True)
        except Exception as error:
            await edit_or_reply(zz, f"{txt}\n**Terjadi Kesalahan Di Log:**\n`{error}`")
            return repo.__del__()
        build = heroku_app.builds(order_by="created_at", sort="desc")[0]
        if build.status == "failed":
            await edit_delete(
                zz, "**Build Gagal!** Dibatalkan karena ada beberapa error.`"
            )
        await edit_or_reply(
            zz, "**تنصيب تحديث زدثـون قيد التقدم... ، يرجى الانتظار حتى تنتهي العملية ، وعادة ما يستغرق التحديث من 4 إلى 5 دقائق.**"
        )

    else:
        return await edit_delete(
            zz, "**[HEROKU]: Harap Tambahkan Variabel** `HEROKU_API_KEY`"
        )


async def update(zz, repo, ups_rem, ac_br):
    try:
        ups_rem.pull(ac_br)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    await edit_or_reply(
        zz, "𓆰 𝗦𝗢𝗨𝗥𝗖𝗘 𝙕𝞝𝘿 - 𝑼𝑷𝑫𝑨𝑻𝑬 𝑴𝑺𝑮 𓆪\n**𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻**\n**⪼ تم التحديث بنجاح ✅**\n ** جارٍ إعادة تشغيل بوت زدثـون ، انتظر 𓆰.**"
    )

    try:
        from userbot.modules.sql_helper.globals import addgvar, delgvar

        delgvar("restartstatus")
        addgvar("restartstatus", f"{zz.chat_id}\n{zz.id}")
    except AttributeError:
        pass

    # Spin a new instance of bot
    args = [sys.executable, "-m", "userbot"]
    execle(sys.executable, *args, environ)


@zed_cmd(pattern="تحديث( الان| البوت|$)")
@register(pattern=r"^\.تحديث( الان| البوت|$)", sudo=True)
async def upstream(event):
    "For .update command, check if the bot is up to date, update if specified"
    zz = await edit_or_reply(event, "𓆰 𝗦𝗢𝗨𝗥𝗖𝗘 𝙕𝞝𝘿 - 𝑼𝑷𝑫𝑨𝑻𝑬 𝑴𝑺𝑮 𓆪\n 𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻\n**⪼ جاري البحث عن التحديثات  🌐.. 𓆰،**")
    conf = event.pattern_match.group(1).strip()
    off_repo = UPSTREAM_REPO_URL
    force_update = False
    try:
        txt = (
            "**Pembaruan Tidak Dapat Di Lanjutkan Karna "
            + "Terjadi Beberapa ERROR**\n\n**LOGTRACE:**\n"
        )
        repo = Repo()
    except NoSuchPathError as error:
        await zz.edit(f"{txt}\n**Directory** `{error}` **Tidak Dapat Di Temukan.**")
        return repo.__del__()
    except GitCommandError as error:
        await zz.edit(f"{txt}\n**Kegagalan awal!** `{error}`")
        return repo.__del__()
    except InvalidGitRepositoryError as error:
        if conf is None:
            return await zz.edit(
                f"**Sayangnya, Directory {error} Tampaknya Bukan Dari Repo. Tapi Kita Bisa Memperbarui Paksa Userbot Menggunakan** `{cmd}update deploy`"
            )
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        force_update = True
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)

    ac_br = repo.active_branch.name
    try:
        repo.create_remote("upstream", off_repo)
    except BaseException:
        pass

    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)

    changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
    if conf == "البوت":
        await zz.edit("`[HEROKU]: Update Deploy Zee-Userbot Sedang Dalam Proses...`")
        await deploy(zz, repo, ups_rem, ac_br, txt)
        return

    if changelog == "" and not force_update:
        await edit_delete(zz, "**✥ Zee-Userbot Sudah Versi Terbaru**")
        return repo.__del__()

    if conf == "" and not force_update:
        await print_changelogs(zz, ac_br, changelog)
        await zz.delete()
        return await event.respond(
            f"**Ketik** `{cmd}update deploy` **untuk Mengupdate Userbot.**"
        )

    if force_update:
        await zz.edit("**Sinkronisasi Paksa Ke Kode Userbot Terbaru, Harap Tunggu...**")

    if conf == "الان":
        for commit in changelog.splitlines():
            if (
                commit.startswith("- [NQ]")
                and HEROKU_APP_NAME is not None
                and HEROKU_API_KEY is not None
            ):
                return await zz.edit(
                    f"**Quick update telah dinonaktifkan untuk pembaruan ini Gunakan** `{cmd}update deploy` **sebagai gantinya.**"
                )
        await zz.edit("𓆰 𝗦𝗢𝗨𝗥𝗖𝗘 𝙕𝞝𝘿 - 𝑼𝑷𝑫𝑨𝑻𝑬 𝑴𝑺𝑮 𓆪\n𓍹ⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧⵧ𓍻\n**⪼ يتم تنصيب التحديث  انتظر 🌐 𓆰،**")
        await update(zz, repo, ups_rem, ac_br)

    return


CMD_HELP.update(
    {
        "update": f"**Plugin : **`update`\
        \n\n  •  **Syntax :** `{cmd}تحديث الان`\
        \n  •  **Function : **Untuk Melihat Pembaruan Terbaru Zee-Userbot.\
        \n\n  •  **Syntax :** `{cmd}تحديث البوت`\
        \n  •  **Function : **Untuk MengUpdate Fitur Terbaru Dari Zee-Userbot.\
    "
    }
)
