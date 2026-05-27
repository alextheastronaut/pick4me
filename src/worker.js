export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.endsWith(".html") || url.pathname.endsWith("/")) {
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
