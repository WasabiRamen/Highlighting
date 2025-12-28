def verify_email_form(code: str, expiry: int) -> str:
    html = f""" 
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>이메일 인증 안내 — Hilighting</title>
    </head>
    <body
        style="font-family:system-ui,-apple-system,Segoe UI,Roboto,'Noto Sans KR',Arial; background:#f6f7fb; margin:0; padding:24px;"
    >
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
            <td align="center">
            <table
                width="600"
                cellpadding="0"
                cellspacing="0"
                role="presentation"
                style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #eceff1;"
            >
                <tr>
                <td style="padding:20px 28px;background:linear-gradient(90deg,#004766,#006a85);color:#fff;">
                    <h1 style="margin:0;font-size:18px;">
                    <span style="font-weight:800;letter-spacing:0.4px;">Hilighting</span>
                    </h1>
                    <div style="font-size:13px;opacity:0.95;margin-top:6px;">이메일 인증 안내</div>
                </td>
                </tr>

                <tr>
                <td style="padding:28px;">
                    <p style="margin:0 0 12px 0;color:#111827;font-size:15px;line-height:1.6;">
                    안녕하세요.<br />
                    회원님께서 요청하신 이메일 인증 코드를 발송해드립니다.
                    </p>

                    <div style="margin:18px 0;text-align:center;">
                    <div
                        style="display:inline-block;padding:18px 22px;border-radius:10px;background:linear-gradient(180deg,#fff 0%,#f2fbfc 100%);border:1px solid rgba(0,71,102,0.06);"
                    >
                        <div style="font-size:22px;color:#004766;font-weight:800;letter-spacing:2px;">
                        {code}
                        </div>
                        <div style="font-size:12px;color:#6b7280;margin-top:6px;">
                        인증번호 (유효시간: {expiry}분)
                        </div>
                    </div>
                    </div>

                    <p style="margin:0 0 12px 0;color:#374151;font-size:14px;line-height:1.6;">
                    위 인증번호를 입력하여 이메일 인증을 완료해 주세요. 인증 요청을 하지
                    않으셨다면 본 메일을 무시하셔도 됩니다.
                    </p>

                    <hr style="border:none;border-top:1px solid #eef2f6;margin:18px 0;" />

                    <p style="margin:0;color:#6b7280;font-size:13px;">
                    도움이 필요하신 경우
                    <a href="mailto:support@hi-light.online" style="color:#004766;text-decoration:none;">
                        support@hi-light.online
                    </a>
                    으로 연락 주세요.
                    </p>
                </td>
                </tr>

                <tr>
                <td style="padding:12px 20px;background:#fafafa;text-align:center;font-size:12px;color:#9ca3af;">
                    © 2025 Hilighting. All rights reserved.
                </td>
                </tr>
            </table>
            </td>
        </tr>
        </table>
    </body>
    </html>
    """
    return html

