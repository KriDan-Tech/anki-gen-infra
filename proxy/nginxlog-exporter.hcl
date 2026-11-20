listen { port = 4040 }

namespace "nginx" {
  source = { files = ["/var/log/nginx/access.log"] }
  format = "$status $request_time $upstream_response_time"
}
