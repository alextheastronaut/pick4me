export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname === "brilla.alextheastronaut.workers.dev") {
      return Response.redirect(`https://plate-up.app${url.pathname}${url.search}`, 301);
    }

    if (url.pathname === "/" || url.pathname === "") {
      return Response.redirect("https://plate-up.app/osun-grill", 301);
    }
    const ext = url.pathname.split("/").pop().includes(".");
    if (!ext || url.pathname.endsWith(".html") || url.pathname.endsWith("/")) {
      const response = await env.ASSETS.fetch(request);
      const html = await response.text();
      const injected = html.replace(
        "</head>",
        `<script>window.PICK4ME_API_BASE="${env.API_BASE}";</script></head>`
      );
      return new Response(injected, {
        status: response.status,
        headers: { "Content-Type": "text/html;charset=UTF-8" },
      });
    }
    return env.ASSETS.fetch(request);
  },
};
