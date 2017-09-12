import sublime, sublime_plugin
from urllib import request
from re import sub
from html.parser import HTMLParser
import time

class HtmlSavingListener(sublime_plugin.EventListener):
   def on_pre_save_async(self, view):
      view.run_command("html_validate")
class HtmlValidateCommand(sublime_plugin.TextCommand):
   def run(self, edit):
      ext = self.view.window().extract_variables()["file_extension"] if "file_extension" in self.view.window().extract_variables() else ""
      if(ext in ["html", "htm"]):
         self.main()

   url = "http://validator.w3.org/nu/"
   head = {"content-type": "text/html; charset=utf-8"}

   replTag = lambda self, s: sub("<[^>]*>", "", s)
   def getBetween(self, s, stt, end):
      b = s.index(stt)+len(stt)
      e = s.index(end, b)
      return s[b:e]

   def convCode(self, s):
      return s.replace("<code>", "&lt;").replace("</code>", "&gt;")
   def main(self):
      with open(self.view.file_name().replace("\\", "/"), "rb") as f:
         req = request.urlopen(request.Request(self.url, data=f.read(), headers=self.head))
         res = req.read().decode()
         self.view.erase_regions("htmlerr")
      if(not "failure" in res):
         self.view.set_status("htmlst", "HTML is valid!")
      else:
         prob = {"error": [], "warning": []}
         regns = []
         find = res
         find = self.getBetween(find, 'id="results"', "</div>")
         find = self.getBetween(find, "<ol>", "</ol>")
         find = find.split("<li")[1:]
         
         content = ""
         for p in find:
            e = {}
            e["type"] = self.getBetween(p, "<strong>", "</strong>")
            e["name"] = HTMLParser().unescape(self.replTag(self.convCode(self.getBetween(p, "<span>", "</span>"))))
            e["loc"] = self.replTag(self.getBetween(p, '<p class="location">', "</p>"))
            e["line"] = [int(p) for p in sub('[^,-9^;]', '', e["loc"]).split(';')[0].split(',')]
            txtp = self.view.text_point(e["line"][0]-1, e["line"][1])
            regns.append(self.view.word(txtp))
            prob[e["type"].lower()].append(e)
         for e in ["error", "warning"]:
            add = "s" if (len(prob[e]) != 1) else ""
            content += "{} {}{}\n".format(len(prob[e]), e.title(), add)
         content += "\n"
         for e in ["error", "warning"]:
            if(len(prob[e]) != 0):
               for p in prob[e]:
                  content += "{}: {}\n{}\n".format(p["type"], p["name"], p["loc"])
                  if(p != prob[e][-1]): content += "\n"
         flags = sublime.DRAW_NO_FILL + sublime.DRAW_NO_OUTLINE + sublime.DRAW_SQUIGGLY_UNDERLINE
         self.view.add_regions("htmlerr", regns, "mcol_B22222FF", "dot", flags)
         self.view.set_status("htmlst", "HTML5 is invalid!")