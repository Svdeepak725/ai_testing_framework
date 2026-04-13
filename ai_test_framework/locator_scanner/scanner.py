import json
from selenium.webdriver.common.by import By

class PageScanner:

    def __init__(self, driver):
        self.driver = driver
        self.locators = []

    def get_xpath(self, element):
        return self.driver.execute_script("""
        function getElementXPath(elt) {
            var path = "";
            for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
                var idx = 0;
                var sib = elt.previousSibling;
                while (sib) {
                    if (sib.nodeType == 1 && sib.tagName == elt.tagName) idx++;
                    sib = sib.previousSibling;
                }
                var tagName = elt.tagName.toLowerCase();
                var part = tagName + (idx ? "[" + (idx+1) + "]" : "");
                path = "/" + part + path;
            }
            return path;
        }
        return getElementXPath(arguments[0]);
        """, element)

    def get_attributes(self, element):
        return self.driver.execute_script("""
        var items={};
        for (let i=0; i < arguments[0].attributes.length; i++){
            items[arguments[0].attributes[i].name] = arguments[0].attributes[i].value;
        }
        return items;
        """, element)

    def get_css_selector(self, element):
        # Generate a human readable CSS selector for the element. Prefer ID if present,
        # otherwise walk up the DOM and build a selector using tag, classes, and nth-child.
        return self.driver.execute_script("""
        function getCssSelector(el) {
            if (!el) return '';
            // Use ID if available (IDs are usually unique)
            if (el.id) return '#' + el.id;

            var parts = [];
            while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== 'html') {
                var tag = el.tagName.toLowerCase();
                var part = tag;

                // Add classes if present
                if (el.classList && el.classList.length > 0) {
                    var cls = Array.prototype.slice.call(el.classList).filter(Boolean).join('.');
                    if (cls) part += '.' + cls;
                }

                var parent = el.parentNode;
                if (parent) {
                    var sameTagSiblings = Array.prototype.filter.call(parent.children, function(child){
                        return child.tagName === el.tagName;
                    });
                    if (sameTagSiblings.length > 1) {
                        // Use nth-child of parent (1-based)
                        var idx = 1;
                        for (var i = 0; i < parent.children.length; i++) {
                            if (parent.children[i] === el) { idx = i + 1; break; }
                        }
                        part += ':nth-child(' + idx + ')';
                    }
                }

                parts.unshift(part);
                el = el.parentNode;
            }
            return parts.join(' > ');
        }
        return getCssSelector(arguments[0]);
        """, element)

    def scan_page(self, output="locators.json"):
        elements = self.driver.find_elements(By.XPATH, "//*")

        for elem in elements:
            try:
                attrs = self.get_attributes(elem)
                text = elem.text.strip()

                data = {
                    "tag": elem.tag_name,
                    "text": text,
                    "attributes": attrs,
                    "xpath": self.get_xpath(elem),
                    "css": self.get_css_selector(elem)
                }
                self.locators.append(data)
            except:
                pass

        with open(output, "w", encoding="utf-8") as f:
            json.dump(self.locators, f, indent=4)

        print("📌 Saved:", output)
