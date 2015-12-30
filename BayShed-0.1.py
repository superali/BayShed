

import gtk
import webkit
import pango
import time
import smtplib
import sys
import time
from datetime import datetime
import sqlite3 as sql
import gobject
import threading
import pycurl
import os
import StringIO
from yapsy.PluginManager import PluginManager

gtk.threads_init()  

db='HDB1'

class Inspector (gtk.Window):
    def __init__ (self, inspector):
        """initialize the WebInspector class"""
        gtk.Window.__init__(self)
        self.set_default_size(600, 480)

        self._web_inspector = inspector

        self._web_inspector.connect("inspect-web-view",
                                    self._inspect_web_view_cb)
        self._web_inspector.connect("show-window",
                                    self._show_window_cb)
        self._web_inspector.connect("attach-window",
                                    self._attach_window_cb)
        self._web_inspector.connect("detach-window",
                                    self._detach_window_cb)
        self._web_inspector.connect("close-window",
                                    self._close_window_cb)
        self._web_inspector.connect("finished",
                                    self._finished_cb)

        self.connect("delete-event", self._close_window_cb)

    def _inspect_web_view_cb (self, inspector, web_view):
        """Called when the 'inspect' menu item is activated"""
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        webview = webkit.WebView()
        scrolled_window.add(webview)
        scrolled_window.show_all()

        self.add(scrolled_window)
        return webview

    def _show_window_cb (self, inspector):
        """Called when the inspector window should be displayed"""
        self.present()
        return True

    def _attach_window_cb (self, inspector):
        """Called when the inspector should displayed in the same
        window as the WebView being inspected
        """
        return False

    def _detach_window_cb (self, inspector):
        """Called when the inspector should appear in a separate window"""
        return False

    def _close_window_cb (self, inspector, view):
        """Called when the inspector window should be closed"""
        self.hide()
        return True

    def _finished_cb (self, inspector):
        """Called when inspection is done"""
        self._web_inspector = 0
        self.destroy()
        return False



class ProgressBar:
    def __init__(self, fname):
        self.round = 0.0
        self.fname=fname
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        win.set_title("Downloads ")
        win.show()
        vbox = gtk.VBox(spacing=5)
        vbox.set_border_width(10)
        win.add(vbox)
        win.set_default_size(300, 50)
        vbox.show()
        self.label = gtk.Label("Downloading %s" % fname)
        self.label.set_alignment(0, 0.5)
        vbox.pack_start(self.label)
        self.label.show()
        pbar = gtk.ProgressBar()
        pbar.show()
        self.pbar = pbar
        vbox.pack_start(pbar)
        win.connect("destroy", self.close_app)
  
    def progress(self, download_t, download_d, upload_t, upload_d):
        unit='b'
        tunit='b'
        
        if download_t == 0:
            self.round = self.round + 0.1
            if self.round >= 1.0:
                self.round = 0.0
        else:
            self.round = float(download_d) / float(download_t)
        if download_d/1024 >1:
            download_d=float(download_d)/1024
            unit='Kb'
            if download_d/1024 >1:
                download_d=download_d/1024
                unit='Mb'
                if download_d/1024 >1:
                    download_d=download_d/1024
                    unit='Gb'
        if download_t/1024 >1:
            download_t=float(download_t)/1024
            tunit='Kb'
            if download_t/1024 >1:
                download_t=download_t/1024
                tunit='Mb'
                if download_t/1024 >1:
                    download_t=download_t/1024
                    tunit='Gb'
        gtk.threads_enter()
        self.pbar.set_fraction(self.round)
        self.label.set_text("Downloading %d %s of %d %s of %s"%(download_d,unit,download_t,tunit,self.fname))
        gtk.threads_leave()        
  
    def close_app(self, *args):
        pass
  
class Download(threading.Thread):
    def __init__(self, url, target_file, progress):
        threading.Thread.__init__(self)        
        self.target_file = target_file
        self.progress = progress
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEDATA, self.target_file)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.NOPROGRESS, 0)
        self.curl.setopt(pycurl.PROGRESSFUNCTION, self.progress)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.NOSIGNAL, 1)
        
    def run(self):
        self.curl.perform()
        self.curl.close()
        self.target_file.close()
        self.progress(1.0, 1.0, 0, 0)  
  

        
def ret(uri,path,fname,fc):
    #Test('file:///c:/xamp2/htdocs/aff/a.mp4', open('H:/jjjjj.jpg', 'wb'), p.progress).start()    
    print path
    path=path[10:]
    print path
    if  os.path.exists(path):
                print 'dialo'
                dialog = Dialog(fc,'Warning','file already exists\ndo you want to over write it?')
                response = dialog.run()
                if response == gtk.RESPONSE_OK:
                    p = ProgressBar(fname)
                    d = Download(uri,open(path,'wb'),p.progress).start()
                dialog.destroy()
    else:
        p = ProgressBar(fname)
        d = Download(uri,open(path,'wb'),p.progress).start()           
            
class MSG:

    def toggle_left_margin(self, checkbutton, textview):
        if checkbutton.get_active():
            textview.set_left_margin(50)
        else:
            textview.set_left_margin(0)

    def toggle_right_margin(self, checkbutton, textview):
        if checkbutton.get_active():
            textview.set_right_margin(50)
        else:
            textview.set_right_margin(0)

    def on_justify(self, button, textview, val):
        textview.set_justification(val)

    def close_application(self, widget):
        return False
    
    def on_clear_clicked(self, widget):
        start,end=self.textbuffer.get_bounds()
        self.textbuffer.remove_all_tags(start, end)

    def on_tag(self, widget, tag):
        bounds = self.textbuffer.get_selection_bounds()
        if len(bounds) != 0:
            start, end = bounds
            self.textbuffer.apply_tag(tag, start, end)
    
    def send(self,w,textview,sender,toentry,subentry,smtpserver):
        reciever=toentry.get_text()
        subject=subentry.get_text()
        header = 'To:' + reciever + '\n' + 'From: ' + sender + '\n' + 'Subject:'+subject + '\n'
        self.textbuffer = textview.get_buffer()
        start,end=self.textbuffer.get_bounds()
        text=self.textbuffer.get_text(start,end)
        msg=header+'\n'+text
        smtpserver.sendmail(sender, reciever, msg)
        print'sent'

    def __init__(self,sender,smtpserver):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_resizable(True)
        window.set_title('Welcome %s'%sender)  

        window.connect("destroy", self.close_application)
        window.set_border_width(0)
        window.set_default_size(800,600)
        box1 = gtk.VBox(False, 0)
        window.add(box1)
        box1.show()
        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()
        address_box=gtk.HBox()
        box2.pack_start(address_box, False, False, 0)
        send_button=gtk.Button('Send')
        tolabel=gtk.Label('TO')
        toentry=gtk.Entry()
        sublabel=gtk.Label('Subject')
        subentry=gtk.Entry() 
        address_box.pack_start(send_button,False)
        address_box.pack_start(subentry,False)
        address_box.pack_start(sublabel,False)
        address_box.pack_start(toentry)
        address_box.pack_start(tolabel,False)
        toolbox = gtk.HButtonBox()
        box2.pack_start(toolbox, False, False, 0)         
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textview.set_editable(True)
        textview.set_cursor_visible(True)
        textview.set_wrap_mode(gtk.WRAP_WORD)
        textview.set_wrap_mode(gtk.WRAP_CHAR)
        textview.set_justification(gtk.JUSTIFY_LEFT)
        self.textbuffer = textview.get_buffer() 
        self.tag_bold = self.textbuffer.create_tag("bold",weight=pango.WEIGHT_BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic",style=pango.STYLE_ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline",underline=pango.UNDERLINE_SINGLE)
        sw.add(textview)
        sw.show()
        textview.show()
        box2.pack_start(sw)
        vbox = gtk.VBox()
        vbox.show()
        toolbox.pack_start(vbox, False, False, 0)         
        check = gtk.CheckButton("Left Margin")
        vbox.pack_start(check, False, False, 0)
        check.connect("toggled", self.toggle_left_margin, textview)
        check.set_active(False)
        check.show()
        check = gtk.CheckButton("Right Margin")
        vbox.pack_start(check, False, False, 0)
        check.connect("toggled", self.toggle_right_margin, textview)
        check.set_active(False)
        check.show() 
        button_bold = gtk.ToolButton(gtk.STOCK_BOLD)
        toolbox.pack_start(button_bold, False, False, 0)
        button_italic = gtk.ToolButton(gtk.STOCK_ITALIC)
        toolbox.pack_start(button_italic, False, False, 0)
        button_underline = gtk.ToolButton(gtk.STOCK_UNDERLINE)
        toolbox.pack_start(button_underline, False, False, 0)
        button_bold.connect("clicked", self.on_tag, self.tag_bold)
        button_italic.connect("clicked", self.on_tag,self.tag_italic)
        button_underline.connect("clicked", self.on_tag,self.tag_underline)
        justifyleft = gtk.ToolButton(gtk.STOCK_JUSTIFY_LEFT)
        toolbox.pack_start(justifyleft, False, False, 0)
        justifycenter = gtk.ToolButton( gtk.STOCK_JUSTIFY_CENTER)
        toolbox.pack_start(justifycenter, False, False, 0)
        justifyright = gtk.ToolButton( gtk.STOCK_JUSTIFY_RIGHT)
        toolbox.pack_start(justifyright, False, False, 0)
        justifyfill = gtk.ToolButton( gtk.STOCK_JUSTIFY_FILL)
        toolbox.pack_start(justifyfill, False, False, 0)        
        justifyright.connect("clicked", self.on_justify,textview,gtk.JUSTIFY_RIGHT)
        justifyfill.connect("clicked", self.on_justify,textview,gtk.JUSTIFY_FILL)
        justifyleft.connect("clicked", self.on_justify,textview,gtk.JUSTIFY_LEFT)
        justifycenter.connect("clicked", self.on_justify,textview,gtk.JUSTIFY_CENTER) 
        button_clear = gtk.ToolButton(gtk.STOCK_CLEAR)
        button_clear.connect("clicked", self.on_clear_clicked)
        toolbox.pack_start(button_clear, False, False, 0)
        toolbox.pack_start(gtk.SeparatorToolItem(), False, False, 0)   
        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        send_button.connect('clicked',self.send,textview,sender,toentry,subentry,smtpserver)
        window.show_all()
    
class Hdb_window(gtk.Window):
    __gsignals__ = {
        
        "open": (gobject.SIGNAL_RUN_LAST,
                                 gobject.TYPE_NONE,
                                 (gobject.TYPE_STRING,)),
        "open-info": (gobject.SIGNAL_RUN_LAST,
                                 gobject.TYPE_NONE,
                                 (gobject.TYPE_INT,))
                                   }
    
    def __init__(self):
        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)        
        self.connect("delete_event", self.delete_event)
        self.set_title('History')
        self.set_default_size(850,400)
        self.h=history()
    def show_log(self):
        scroll=gtk.ScrolledWindow()
        box=gtk.VBox()
        hbox=gtk.HBox()
        del_btn=gtk.ToolButton(gtk.STOCK_DELETE)
        del_btn.set_tooltip(gtk.Tooltips(),('Delete'))
        inf_btn=gtk.ToolButton(gtk.STOCK_INFO)
        inf_btn.set_tooltip(gtk.Tooltips(),('Show More Information'))
        inf_btn.connect('clicked',self.show_info)
        del_btn.connect('clicked',self.del_history)
        box.pack_start(hbox,False)
        open_btn=gtk.ToolButton(gtk.STOCK_OK)
        open_btn.set_tooltip(gtk.Tooltips(),('Open Website'))
        open_btn.connect('clicked',self.open_cb)
        hbox.pack_start(open_btn,False)
        hbox.pack_start(inf_btn,False)
        hbox.pack_start(del_btn,False)
        box.add(scroll)        
        self.add(box)        
        self.store=gtk.ListStore(str,str,str,str,int)
        self.info=self.h.connect()        
        if len(self.info) > 0:
           x = 0;
           while x < len(self.info):
               self.store.append([self.info[x][0],self.info[x][1],self.info[x][2],self.info[x][3],self.info[x][4]]);
               x += 1;
        self.treeview=gtk.TreeView(self.store)
        date_column=gtk.TreeViewColumn('Date',gtk.CellRendererText(),text=0)
        date_column.set_sort_column_id(0)
        self.treeview.append_column(date_column)        
        column=gtk.TreeViewColumn('  Time',gtk.CellRendererText(),text=1)
        self.treeview.append_column(column)        
        web_column=gtk.TreeViewColumn('  WebSite',gtk.CellRendererText(),text=2);
        web_column.set_sort_column_id(2)
        self.treeview.append_column(web_column)
        column=gtk.TreeViewColumn('  URL',gtk.CellRendererText(),text=3);
        self.treeview.append_column(column)        
        v_column=gtk.TreeViewColumn('  visit_count',gtk.CellRendererText(),text=4)
        v_column.set_sort_column_id(4)        
        self.treeview.append_column(v_column)                
        scroll.add(self.treeview)
        #self.show_all()
        return self.treeview,self.store
        
    def add_history(self,site_url,last_v_time,v_date):
        b=site_url.find('.')
        c=site_url.find('.',b+1)
        
        title=site_url[b+1:c]
        ex=False
        x=0
        self.info=self.h.connect()
        while x < len(self.info):
            if self.info[x][2]==title:
                self.update(v_date,last_v_time ,title,site_url ,self.info[x][4] ,self.info[x][5])
                ex=True
                break
            x+=1
        if ex==False:
            self.h.insert(site_url,last_v_time,v_date,title)
            
    def show_info(self,title):
        self.emit('open-info',1)
        
    def del_history(self,w):
        select = self.treeview.get_selection();
        ar = select.get_selected();
        uri = ar[0].get_value(ar[1],3);
        self.h.delete(uri)
        self.store.remove(ar[1])
            
    def delete_event(self, widget, event, data=None):
        pass
    def open_cb(self,w):
        select = self.treeview.get_selection();
        ar = select.get_selected();
        uri = ar[0].get_value(ar[1],3);
        self.emit('open',uri)
    def update(self,v_date,v_time ,title,site_url ,visit_count ,web_id):
        self.h.update(v_date,v_time ,title,site_url ,visit_count ,web_id)

class Hdb_info(gtk.Window):
    __gsignals__ = {
        
        "open": (gobject.SIGNAL_RUN_LAST,
                                 gobject.TYPE_NONE,
                                 (gobject.TYPE_STRING,))

                                   
                                   }
    
    def __init__(self,tree):
        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)        
        self.connect("delete_event", self.delete_event)
        self.set_title('Info')
        self.set_default_size(750,300)
        self.h=history()
        self.tree=tree
            
    def show_info(self):
        select =self.tree.get_selection();
        ar = select.get_selected();
        title = ar[0].get_value(ar[1],2);
        scroll=gtk.ScrolledWindow()
        box=gtk.VBox()
        hbox=gtk.HBox()
        box.pack_start(hbox,False)
        open_btn=gtk.ToolButton(gtk.STOCK_OK)
        open_btn.set_tooltip(gtk.Tooltips(),('Open URL'))
        open_btn.connect('clicked',self.open_cb)
        hbox.pack_start(open_btn,False)
        box.add(scroll)
        del_btn=gtk.ToolButton(gtk.STOCK_DELETE)
        del_btn.set_tooltip(gtk.Tooltips(),('Delete'))
        hbox.pack_start(del_btn,False)
        self.add(box)
        self.s=gtk.ListStore(str,str,str,str)
        self.info=self.h.connect(title)        
        if len(self.info) > 0:
           x = 0;
           while x < len(self.info):
               self.s.append([self.info[x][0],self.info[x][1],self.info[x][2],self.info[x][3]]);
               x += 1;
        self.treeview=gtk.TreeView(self.s)
        date_column=gtk.TreeViewColumn('Date',gtk.CellRendererText(),text=0)
        date_column.set_sort_column_id(0)
        self.treeview.append_column(date_column)        
        column=gtk.TreeViewColumn('  Time',gtk.CellRendererText(),text=1)
        self.treeview.append_column(column)        
        web_column=gtk.TreeViewColumn('  WebSite',gtk.CellRendererText(),text=2);
        web_column.set_sort_column_id(2)
        self.treeview.append_column(web_column)
        column=gtk.TreeViewColumn('  URL',gtk.CellRendererText(),text=3);
        self.treeview.append_column(column)        
        del_btn.connect('clicked',self.del_history,True)        
        scroll.add(self.treeview)
        self.set_size_request(500,300)
        return self.treeview,self.s
        
    def del_history(self,w,child=None):
        select = self.treeview.get_selection();
        ar = select.get_selected();
        uri = ar[0].get_value(ar[1],3);
        self.h.delete(uri,child)
        self.s.remove(ar[1])
            
    def delete_event(self, widget, event, data=None):
        pass
    def open_cb(self,w):
        select = self.treeview.get_selection()
        ar = select.get_selected();
        uri = ar[0].get_value(ar[1],3);
        self.emit('open',uri)
        
class history():
    def connect(self,title=None):
        self.con=sql.connect(db)
        if title:
            self.cur=self.con.execute('SELECT v_date,visit_time ,title,site_url from visits where title="'+title+'"')
        else:
            self.cur=self.con.execute('''SELECT
                      
                      last_v_date,
                      last_visit_time ,
                      title,
                      url ,
                      visit_count ,
                      id from urls''')
        array=self.cur.fetchall()
        self.con.close()
        
        return array       

    def insert(self,site_url,last_v_time,last_v_date,title):
        self.con=sql.connect(db)
        try:
            with self.con:
                self.con.execute('''INSERT INTO urls (
                      
                      url,
                      last_visit_time,
                      last_v_date,
                      title,
                      visit_count)  
                      VALUES (?,?,?,?,?)''',(site_url, last_v_time,last_v_date,title,1))
        except sql.IntegrityError:
                print'452'
        except Exception as e:
                self.con.rollback()
                raise e
        else:    
             self.con.commit()
        finally:
            self.con.close()


    def delete(self,uri,child=None):
        self.con=sql.connect(db)
        if child:
            self.con.execute('DELETE from visits where site_url="'+uri+'"')
        else:
            self.con.execute('DELETE from urls where url="'+uri+'";')
        self.con.commit()
        self.con.close()
       
    def update(self,v_date,v_time ,title,site_url ,visit_count ,web_id):
        self.con=sql.connect(db)

        self.con.execute('UPDATE urls set last_visit_time ="'+v_time+'", last_v_date ="'+v_date+'" where title="'+title+'"')
        self.con.commit()

        self.con.execute('UPDATE urls set visit_count =visit_count+1 where title="'+title+'"')
        
        self.con.commit()
        try:
            with self.con:
                self.con.execute('''INSERT INTO visits (
                      
                url_id ,
                title ,
                site_url,
                v_date  ,
                visit_time   )  
                      VALUES (?,?,?,?,?)''',(web_id,title,site_url,v_date,v_time))
        except sql.IntegrityError:
                print'452'
        except Exception as e:
                self.con.rollback()
                raise e
        else:    
             self.con.commit()
        finally:
            self.con.close()
        
class Dialog(gtk.Dialog):

    def __init__(self, parent,title,message):
        self.message=message
        self.head=title
        gtk.Dialog.__init__(self, self.head, parent, 0,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK))

        self.set_default_size(150, 100)

        label = gtk.Label(self.message)

        box = self.get_content_area()
        box.add(label)
        self.show_all()
        
class TabLabel (gtk.HBox):
    __gsignals__ = {
        "close": (gobject.SIGNAL_RUN_FIRST,
                  gobject.TYPE_NONE,
                  (gobject.TYPE_OBJECT,))
    
        }        

    def __init__ (self, title, child):
        gtk.HBox.__init__(self, False, 4)
        self.title = title
        self.child = child
        self.label = gtk.Label(title)
        
        self.label.props.max_width_chars = 30
        self.label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.label.set_alignment(0.0, 0.5)

        icon = gtk.image_new_from_stock(gtk.STOCK_ORIENTATION_PORTRAIT, gtk.ICON_SIZE_MENU)
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        close_button = gtk.Button()
        close_button.set_relief(gtk.RELIEF_NONE)
        
        close_button.connect("clicked", self._close_tab, child)
        close_button.add(close_image)
        self.pack_start(icon, False, False, 0)
        self.pack_start(self.label, True, True, 0)
        self.pack_start(close_button, False, False, 0)

        self.set_data("label", self.label)
        self.set_data("close-button", close_button)
        self.connect("style-set", tab_label_style_set_cb)

    def set_label_text(self, text):
        self.label.set_label(text)

    def _close_tab (self, widget, child):
        self.emit("close", child)

class Console (gtk.Notebook):

    __gsignals__ = {
        "focus-view-title-changed": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT,
                                      gobject.TYPE_STRING,gobject.TYPE_OBJECT,)
                        ),
        }

    def __init__ (self,page=None):
        gtk.Notebook.__init__(self)
        self.props.scrollable = True
        self.props.homogeneous = True
        self.connect("switch-page", self.switch_page)
        #self.connect("populate-popup",self.populate_popup)
        self.scroll=gtk.ScrolledWindow()
    
        self.show_all()        

        
    def switch_page (self, notebook, page, page_num):
        child = self.get_nth_page(page_num)
        view = child.get_child()
        frame = view.get_main_frame()
        self.emit("focus-view-title-changed", frame, frame.props.title,view)

        
class BrowserPage(webkit.WebView):
       
    __gsignals__ = {
        
        "new-window-requested": (gobject.SIGNAL_RUN_FIRST,
                                 gobject.TYPE_NONE,
                                 (gobject.TYPE_OBJECT,)),
        "tab-request":(gobject.SIGNAL_RUN_FIRST,
                       gobject.TYPE_NONE,
                       (gobject.TYPE_OBJECT,))

                           }
    def __init__(self):
        webkit.WebView.__init__(self)
        settings = self.get_settings()
        settings.set_property("enable-developer-extras", True)
        settings.set_property('user-agent', 'BayShed 1.0')
        settings.set_property('enable-spell-checking',True)
        settings.set_property('enable-spatial-navigation',True)
        
        settings.set_property("enable-plugins", True)
        self.set_settings(settings)
        self.set_full_content_zoom(True)
        self.connect_after("populate-popup", self.populate_popup)
                
    def populate_popup(self,view, menu):
        if BROWSER.tab_url :                
            open_in_new_tab = gtk.MenuItem(("Open Link in New Tab"))
            open_in_new_tab.connect("activate",self.tab_request, view)
            menu.insert(open_in_new_tab, 0)
            BROWSER.tab_url=None        
        zoom_in = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
        zoom_in.connect('activate',zoom_in_cb, view)
        menu.append(zoom_in)
        zoom_out = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
        zoom_out.connect('activate', zoom_out_cb, view)
        menu.append(zoom_out)
        zoom_hundred = gtk.ImageMenuItem(gtk.STOCK_ZOOM_100)
        zoom_hundred.connect('activate',zoom_hundred_cb, view)
        menu.append(zoom_hundred)
        printitem = gtk.ImageMenuItem(gtk.STOCK_PRINT)
        menu.append(printitem)
        printitem.connect('activate',print_cb, view)
        menu.append(gtk.SeparatorMenuItem())
        aboutitem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menu.append(aboutitem)
        aboutitem.connect('activate',about_pywebkitgtk, view)
        menu.show_all()
        return False

    def tab_request(self,mi,v):
        self.emit("tab-request",v)
        
    def get_html(self):
        self.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html=self.get_main_frame().get_title()
        self.execute_script('document.title=oldtitle;')
        return html
    
class BROWSER(gtk.Window,threading.Thread):
    full=None
    patterns=['mp4','pdf','zip','exe']
    private_browsing=None
    home_page='http://google.com'
    url=None
    tab_url=None

    
    __gsignals__ = {
        "new-win": (gobject.SIGNAL_RUN_FIRST,
                  gobject.TYPE_NONE,
                  (gobject.TYPE_STRING,)),
        "download-file":(gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE,
                         (gobject.TYPE_OBJECT,)),
         "enable-caret":(gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE,
                         (gobject.TYPE_STRING,)),
         "enable-private":(gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE,
                         (gobject.TYPE_STRING,)),
        "new-h":(gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE,
                         (gobject.TYPE_INT,)),
         "update-h":(gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE,
                         (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING))
 
 

 
        
        }        

    def about(self, widget):
        about = gtk.AboutDialog()
        about.set_program_name("BayShed")
        about.set_version("0.1")
        about.set_copyright("(c) Ali Al-baiti ")
        about.set_website("http://www.python.org")
        about.set_logo(gtk.gdk.pixbuf_new_from_file("94.jpg"))
        about.run()
        about.destroy()
     
    def go_back(self,w):
        
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        view = child.get_child()        
        if view.can_go_back ():
           view.go_back ()         
        
    def go_forward(self,w):
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        view = child.get_child()        
        if view.can_go_forward ():
           view.go_forward ()
            
    def new_web_view_ready(self, web_view,data=None):
        web=web_view
        self.page.emit("new-window-requested",web)

    def new_window_from_menu(self, w):
        self.emit('new-win',None)

    def new_web_view_request(self, web_view, web_frame):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        view = BrowserPage()
        scrolled_window.add(view)
        scrolled_window.show_all()
        vbox = gtk.VBox(spacing=1)
        vbox.pack_start(scrolled_window, True, True)
        window = gtk.Window()
        window.add(vbox)
        view.connect("web-view-ready", self.new_web_view_ready)
        return view
    
    def open_in_new_tab (self, menuitem,view):
        thread=threading.Thread(target=(self.new_tab()))
        thread.start()
        
    def new_tab_from_m(self,w):
        thread=threading.Thread(target=(self.new_tab()))
        thread.start()
        
    def new_tab (self, uri=None):
        page = BrowserPage()
        if uri:
            self.construct_tab(page, uri)
        else:      
            self.construct_tab(page, BROWSER.url)
            
    def check_uri(self,uri):
        if uri:
            for x in BROWSER.patterns:
                if uri.endswith('.%s'%x):
                    fc = gtk.FileChooserDialog(title="Save file as...", parent=None, buttons=(gtk.STOCK_SAVE, gtk.RESPONSE_OK,gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL), action=gtk.FILE_CHOOSER_ACTION_SAVE)
                    fc.set_default_response(gtk.RESPONSE_OK)
                    fname = 'ali.%s'%x
                    fc.set_current_name(fname)
                    res = fc.run()
                    if  res == gtk.RESPONSE_OK:
                        path = fc.get_uri()
                    fc.destroy()
                    thread=threading.Thread(target=ret(uri,path,fname,fc))
                    thread.start()
                    return True
        return False
    
    def construct_tab(self,web_view,uri=None):        
        flag=self.check_uri(uri)
        if flag:
            return True
        if web_view.can_go_back():
            self.back.set_sesitive(True)
        if web_view.can_go_forward():
            self.forward.set_sesitive(True)            
        web_view.connect("hovering-over-link", hover_over_link)
        web_view.connect("load-finished", self.view_load_finished)
        web_view.connect("create-web-view", self.new_web_view_request)
        web_view.connect('download-requested', self.download_destination)
        web_view.connect('title-changed',self.new_title)
        web_view.connect('load-committed',self.on_click_link)
        web_view.connect("new-window-requested", self.new_window_pop)        
        web_view.connect('load-progress-changed',self.loading_progress_cb)
        web_view.connect('load-started', self.loading_start)
        web_view.connect("tab-request", self.open_in_new_tab)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.add(web_view)
        scrolled_window.show_all()
        inspector = Inspector(web_view.get_web_inspector())        
        # create the tab
        label = TabLabel(uri, scrolled_window)
        label.connect("close", self.close_tab)        
        label.show_all()        
        new_tab_number = self.tabs.append_page(scrolled_window,label)
        self.tabs.set_tab_label_packing(scrolled_window, False, False, gtk.PACK_START)
        self.tabs.set_tab_label(scrolled_window,label)
        self.tabs.set_show_tabs(True)
        self.tabs.set_current_page(new_tab_number)
        self.tabs.set_show_tabs(self.tabs.get_n_pages() > 1)
        if not uri:
            web_view.load_string('', "text/html", "iso-8859-15", "about : blank")
            uri = "about:blank"
        else:
            web_view.load_uri(uri)
        self.addressbar.set_text(uri)
        
    def new_window_pop(self, w,ur):
        self.emit('new-win',BROWSER.url)
        
    def new_window(self, w,uri=None):
        self.emit('new-win',uri)
        
    def open_file(self,w):
        fc = gtk.FileChooserDialog(title="Open file", parent=None, buttons=(gtk.STOCK_OPEN, gtk.RESPONSE_OK,gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL), action=gtk.FILE_CHOOSER_ACTION_OPEN)
        fc.set_default_response(gtk.RESPONSE_OK)        
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        fc.add_filter(filter)        
        filter = gtk.FileFilter()
        filter.set_name("HTML")
        filter.add_mime_type("Web_Doc/html")
        filter.add_pattern("*.html")        
        fc.add_filter(filter)        
        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.gif")
        filter.add_pattern("*.tif")
        filter.add_pattern("*.xpm")
        fc.add_filter(filter)
        res = fc.run()
        if  res == gtk.RESPONSE_OK:
            uri = fc.get_uri()
            print uri
            self.page.open(uri)
        fc.destroy()
        return True
        
    def on_click_link(self,view,frame):
        uri=frame.get_uri()
        self.addressbar.set_text(uri)

    def new_title(self,view,frame,title):
        self.set_title(("BayShed - %s") % title)
        can_go_forward=view.can_go_forward ()
        can_go_back=view.can_go_back ()  
        self.forward.set_sensitive(can_go_forward)
        self.back.set_sensitive(can_go_back)
        uri=frame.get_uri()
        if not BROWSER.private_browsing:
            self.update_history(uri)
                   
    def title_changed(self,console,frame, title,view):
        child = self.tabs.get_nth_page(self.tabs.get_current_page())        
        title = frame.get_title()
        uri=frame.get_uri()
        if uri:
            self.addressbar.set_text(uri)
        else:
            self.addressbar.set_text('about:blank')
        if not title:
           title = frame.get_uri()
        self.set_title(("BayShed - %s") % title)
        can_go_forward=view.can_go_forward ()
        can_go_back=view.can_go_back ()  
        self.forward.set_sensitive(can_go_forward)
        self.back.set_sensitive(can_go_back)            
            
    def go(self,x):
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        view = child.get_child()        
        add=self.addressbar.get_text()
        flag=self.check_uri(add)
        if flag:
            return True
        if add.startswith('http://') or add.startswith('https://'):
            view.open(add)
        else:            
            add='http://'+add
            self.addressbar.set_text(add)
            view.open(add)
        if not BROWSER.private_browsing:
            self.update_history(add)
               
    def Save_as(self, w):
        fc = gtk.FileChooserDialog(title="Save as...", parent=None, buttons=(gtk.STOCK_SAVE, gtk.RESPONSE_OK,gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL), action=gtk.FILE_CHOOSER_ACTION_SAVE)
        fc.set_default_response(gtk.RESPONSE_OK)
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        view = child.get_child()        
        res = fc.run()
        if  res == gtk.RESPONSE_OK:
            html=view.get_html()
            fname=fc.get_filename()
            uri = fc.get_uri()
            print html
            uri=uri[8:]
            data = open(uri+'.html','wb')
            data.write(html)
        fc.destroy()
        return True        
  
    def download_destination(self, view, download):
        self.emit('download-file',download)  
        return True
 
    def close(self,w):
        self.destroy()
        return 0
    
    def close_tab (self, label, child):
        page_num = self.tabs.page_num(child)
        if page_num != -1:
            view = child.get_child()
            view.destroy()
            self.tabs.remove_page(page_num)
            self.tabs.set_show_tabs(self.tabs.get_n_pages() > 1)

    def view_load_finished(self, view, frame):
        self.progressBar.hide()
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        label = self.tabs.get_tab_label(child)
        title = frame.get_title()
        if not title:
           title = frame.get_uri()
        if title:
            label.set_label_text(title)
            self.set_title(("BayShed - %s") % title)
        self.show_reload_icon()
        self.stop_and_reload.set_tooltip(gtk.Tooltips(), ('Reload'))        
        self.loading=False

    def loading_progress_cb(self, view, progress):
        self.progressBar.set_fraction(progress/100.0)
            
    def stop_and_reload_cb(self, button):
        child = self.tabs.get_nth_page(self.tabs.get_current_page())
        view = child.get_child()            
        if self.loading:
            view.stop_loading ()        
        else:
            view.reload()

    def show_stop_icon(self):
        self.stop_and_reload.set_stock_id(gtk.STOCK_CANCEL)
        
    def show_reload_icon(self):
        self.stop_and_reload.set_stock_id(gtk.STOCK_REFRESH)

    def loading_start(self, view, frame):
        self.progressBar.show()
        self.show_stop_icon()
        self.stop_and_reload.set_tooltip(gtk.Tooltips(), ('Stop'))        
        self.loading=True

    def view_source_mode(self,widget):
        currentTab = self.tabs.get_nth_page(self.tabs.get_current_page())
        childView = currentTab.get_child()
        mode=childView.get_view_source_mode()
        if childView:
            childView.set_view_source_mode(not mode)
            childView.reload()

    def show_history(self,w):
        self.emit('new-h',1)
        
    def update_history(self,uri):
        if uri.startswith('about : blank'):
            return
        v_time=str(datetime.now().time())
        v_date=str(datetime.now().date())
        self.emit('update-h',uri,v_time,v_date)

    def enable_private_browsing(self,w):
        if w.active:
            self.emit('enable-private','private_enabled')
        else:
            self.emit('enable-private','private_disabled')
            
    def enable_caret_browsing(self,w):
        if w.active:
            self.emit('enable-caret','caret_enabled')
        else:
            self.emit('enable-caret','caret_disabled')
    
    def send_email(self,w):       
        win=gtk.Window()
        win.set_default_size(300,200)
        win.set_title('Login')
        box=gtk.VBox()
        box2=gtk.HBox()         
        uentry=gtk.Entry()
        pentry=gtk.Entry()
        ulabel=gtk.Label('Your Email')
        plabel=gtk.Label('Password')
        box2.pack_start(ulabel,False)
        box2.pack_start(uentry)
        box.pack_start(box2,False)
        box2=gtk.HBox()
        box2.pack_start(plabel,False)
        box2.pack_start(pentry)
        box.pack_start(box2,False)
        login=gtk.Button('Login')
        login.connect('clicked',self.log_in,uentry,pentry,win)
        box.pack_start(login,False)
        win.add(box)
        win.show_all()
        
    def log_in(self,w,uentry,pentry,win):
        hosts={
               'hotmail.com'        : 'smtp.live.com',
               'gmail.com'          :'smtp.gmail.com',
               'yahoo.it'           :'smtp.mail.yahoo.it',
               'yahoo.es'           :'smtp.mail.yahoo.es',
               'yahoo.de'           :'smtp.mail.yahoo.de',
               'yahoo.co.uk'        :'smtp.mail.yahoo.co.uk',
               'yahoo.com.ar'       :'smtp.mail.yahoo.com.ar',
               'ya.com'             :'smtp.ya.com',
               'xtra.co.nz'         :'smtp.xtra.co.nz',
               'xs4all.nl'          :'mail.xs4all.nl',
               'x-privat.org'       :'mail.x-privat.org',
               'tol.it'             :'smtp-tol.it',
               'qos.net.il'         :'mail.qos.net.il',
               'wooow.it'           :'smtp.wooow.it',
               'zonnet.nl'          :'smtp.zonnet.nl',
               'znet.com'           :'mail.znet.com',
               'ziplink.net'        :'smtp.ziplink.net',
               'zero.ad.jp'         :'zero.ad.jp',
               'zeelandnet.nl'     :'mail.zeelandnet.nl',
               'yahoo.com.cn'       :'smtp.mail.yahoo.com.cn',
               'which.net'          :'mail.which.net',
               'Webmail.is'         :'smtp.emailsrvr.com',
               'web.de'             :'smtp.web.de',
               'wayport.net'        :'mail.wayport.net',
               'wanadoo.nl'         :'smtp.wanadoo.nl',
               'wanadoo.es	'   :'smtp.wanadoo.es	',
               'wanadoo.fr	'   :'smtp.wanadoo.fr	',
               'wanadooadsl.net	'   :'smtp.wanadooadsl.net	',
               'waitrose.com	'   :'smtpmail.waitrose.com	',
               'vodafone.it	'   :'smtpmail.vodafone.it	',
               'vodafone.net	'   :'mail.vodafone.net	',
               'vispa.com	'   :'mail.vispa.com	',
               'vt.edu	'           :'smtp.vt.edu	',
               'virgin.net	'   :'smtp.virgin.net	',
               'videobank.it	'   :'videobank.it		',
               'cs.interbusiness.it':'mail.cs.interbusiness.it	',
               'utopiasystems.net'  :'smtp.utopiasystems.net	',
               'postoffice.net	'   :'smtp.postoffice.net	',
               'postoffice.net	'   :'smtp.postoffice.net	',
               'warpdriveonline.com ':'smtp.warpdriveonline.com	',
               'uol.com.br'         :'smtp.uol.com.br	',
               'gl.umbc.edu'        :'smtp.gl.umbc.edu',
               'umd.edu	'           :'mail.umd.edu	',
               'access4less.net	'   :'smtp.access4less.net	',
               'activenetwork.it'   :'smtp.activenetwork.it	',
               'actrix.co.nz	'   :'mail.actrix.co.nz	',
               'blk.adelphia.net'   :'smtp.blk.adelphia.net',
               ' airtelbroadband.in '   :' smtp.airtelbroadband.in ',
               'albacom.net	'   :'smtp.albacom.net	',
               'alcotek.it	'   :'smtp.alcotek.it	',
               'aol.com	'           :'smtp.aol.com	',
               'arnet.com.ar	'   :'smtp.arnet.com.ar	',
               'aruba.it	'   :'smtp.aruba.it	',
               'attwireless.net	'   :'smtp.attwireless.net	',
               'att.yahoo.com	'   :'smtp.att.yahoo.com	',
               'atlavia.it'         :'smtp.atlavia.it',
               'atlanticbb.net	'   :'smtp.atlanticbb.net	',
               'auna.com	'   :'smtp.auna.com	',
               'batelco.com.bh	'   :'batelco.com.bh	',
               'bestweb.net	'   :'smtp.bestweb.net	',
               'bev.net	'           :'smtp.bev.net	',
               'blacksburg.net	'   :'smtp.blacksburg.net	',
               'blazenet.net	'   :'smtp.blazenet.net	',
               'bezeqint.net	'   :'mail.bezeqint.net	',
               'blu.it	'           :'smtp.blu.it	',
               'mybluelight.com	'   :'smtp.mybluelight.com	',
               'blueyonder.co.uk'   :'smtp.blueyonder.co.uk	',
               'bol.com.br	'   :'smtp.bol.com.br	',
               'brturbo.com.br	'   :'smtp.brturbo.com.br	',
               'cais.net	'   :'smtp.cais.net	',
               'callsouth.net.nz'   :'smtp2.callsouth.net.nz	',
               'calweb.com	'   :'smtp.calweb.com	',
               'capu.net	'   :'smtp.capu.net	',
               'cegetel.net	'   :'smtp.cegetel.net	',
               'charm.net	'   :'smtp.charm.net	',
               'charter.net	'   :'smtp.charter.net	',
               'cheapnet.it	'   :'smtp.cheapnet.it	',
               'choicehotels.com'   :'smtp.choicehotels.com',
               'mymmode.com	'   :'smtp.mymmode.com	',
               'swva.net	'   :'smtp.swva.net	',
               'ciudad.com.ar	'   :'smtp.ciudad.com.ar	',
               'clear.net.nz	'   :'smtp.clear.net.nz	',
               'click21.com.br	'   :'smtp.click21.com.br	',
               'columbia.edu	'   :'smtp.columbia.edu	',
               'comcast.net'        :'smtp.comcast.net',
               'site1.csi.com	'   :'smtp.site1.csi.com	',
               'concentric.net	'   :'smtp.concentric.net	',
               'covad.net	'   :'smtp.covad.net	',
               'east.cox.net	'   :'smtp.east.cox.net	',
               'central.cox.net	'   :'smtp.central.cox.net	',
               'west.cox.net	'   :'smtp.west.cox.net	',
               'crosslink.net	'   :'smtp.crosslink.net	',
               'cultura.com.br	'   :'smtp.cultura.com.br	',
               'ntlworld.com	'   :'smtp.ntlworld.com	',
               'dca.net	'           :'smtp-relay.dca.net	',
               'deltanet.com	'   :'smtp.deltanet.com	',
               'etmail.it	'   :'smtp.etmail.it	',
               'direcway.com	'   :'smtp.direcway.com	',
               'dslextreme.com	'   :'smtp.dslextreme.com	',
               'easynet.co.uk	'   :'smtp.easynet.co.uk	',
               'elitel.biz	'   :'smtp.elitel.biz	',
               'enter.net	'   :'smtp.enter.net	',
               'euronet.nl	'   :'smtp.euronet.nl	',
               'tiscali.it	'   :'smtp.tiscali.it	',
               'ezy.et'             :'smtp.ezy.et	',
               'ezysurf.co.nz	'   :'smtp.ezysurf.co.nz	',
               'fibertel.com.ar	'   :'smtp.fibertel.com.ar	',
               'free.fr	'            :'smtp.free.fr	',
               'freemail.it '       :'smtp.freemail.it	',
               'frontier.com	'   :'smtp.frontier.com	',
               'fcc.net	'           :'smtp.fcc.net	',
               'fullchannel.net	'   :'smtp.fullchannel.net	',
               'galactica.it	'   :'smtp.galactica.it	',
               'gateway.net	'   :'smtp.gateway.net	',
               'giga.net.tw'        :'smtp.giga.net.tw',
               'globe.net.nz'       :'smtp.globe.net.nz	',
               'go.com	'           :'smtp.go.com	',
               'haier-electronics.com':'smtp.haier-electronics.com	',
               'homesteadmail.com'  :'smtp.homesteadmail.com	',
               'hotpop.com  '       :'smtp.hotpop.com	',
               'hva.nl	'           :'smtp.hva.nl	',
               'ibm.net	'           :'smtp1.ibm.net	',
               'ic24.net	'   :'smtp.ic24.net	',
               'ig.com.br	'   :'smtp.ig.com.br	',
               'ihug.co.nz	'   :'smtp.ihug.co.nz	',
               'inet.it	'           :'inet.it	',
               'grrtech.com	'   :'smtp.grrtech.com	',
               'mind.net	'   :'smtp.mind.net	',
               'medford.net	'   :'smtp.medford.net	',
               'kfalls.net	'   :'smtp.kfalls.net	',
               'integra.net	'   :'smtp.integra.net	',
               'interaccess.com	'   :'smtp.interaccess.com',
               'ihwy.com	'   :'smtp.ihwy.com	',
               'internetlibero.it'  :'smtp.internetlibero.it',
               'domain.ext	'   :'smtp.domain.ext	',
               'iprimus.com.au	'   :'smtp.iprimus.com.au',
               'iprolink.co.nz	'   :'smtp.iprolink.co.nz',
               'ixpres.com	'   :'smtp.ixpres.com	',
               'juno.com	'   :'smtp.juno.com	',
               'katamail.com	'   :'smtp.katamail.com	',
               'laposte.net	'   :'smtp.laposte.net	',
               'neuf.fr	'           :'smtp.neuf.fr	',

                'mail.ru'           :'smtp.mail.ru',
              }

        user=uentry.get_text()
        password=pentry.get_text()
        i=user.find('@')
        h=user[i+1:]
        host=hosts.get(h)
        if host:
            smtpserver = smtplib.SMTP(host,587)
        else :
            dialog=Dialog(win,'unidetified Server','invalid unsupported server')
            r=dialog.run()
            dialog.destroy()
            return 0
        try:
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo
            smtpserver.login(user, password)
            flag=True
        except Exception :
            return
        if flag:
            self.write_msg(user,smtpserver)
            win.destroy()        
        
    def write_msg(self,sender,smtpserver):
        msg=MSG(sender,smtpserver)
               
    def search(self,w):
        tab=self.tabs.get_nth_page(self.tabs.get_current_page())
        view=tab.get_child()
        entry=self.search_bar.get_text()
        view.open('https://www.google.com/?gws_rd=ssl#q=%s'%entry)
        
    def go_home(self,w):
        tab=self.tabs.get_nth_page(self.tabs.get_current_page())
        view=tab.get_child()
        view.open(BROWSER.home_page)
    def full_screen(self,w):
        if  w.active :
            self.fullscreen()
            BROWSER.full=True
        else:
            self.unfullscreen()
            BROWSER.full=False
    def full_key(self,w,event):
        if event.keyval == gtk.keysyms.F11:
            if BROWSER.full:
                self.unfullscreen()
                BROWSER.full=False
            else:
                self.fullscreen()
                BROWSER.full=True
                
    def __init__(self,url=None):
        threading.Thread.__init__(self)
        gtk.Window.__init__(self)
               
        self.mb = gtk.MenuBar()

        filemenu = gtk.Menu()
        filem = gtk.MenuItem("File")
        filem.set_submenu(filemenu)
        Toolsm=gtk.Menu()
        Tools=gtk.MenuItem("Tools")
        Tools.set_submenu(Toolsm)
        Sende = gtk.MenuItem("Send Email")
        Sende.connect("activate", self.send_email)
        Toolsm.append(Sende)

        Helpm=gtk.Menu()
        Help=gtk.MenuItem("Help")
        Help.set_submenu(Helpm)
        About = gtk.MenuItem("About")
        About.connect("activate", self.about)
        Helpm.append(About) 
        viewmenu = gtk.Menu()
        
        view = gtk.MenuItem("View")
        view.set_submenu(viewmenu)
        Optionsm=gtk.Menu()
        Options=gtk.MenuItem("Options")
        Options.set_submenu(Optionsm)

        en_pr = gtk.CheckMenuItem("Enable Private Browsing")
        en_pr.connect("activate", self.enable_private_browsing)
        Optionsm.append(en_pr)
        en_c = gtk.CheckMenuItem("Enable Caret Browsing")
        en_c.connect("activate", self.enable_caret_browsing)
        Optionsm.append(en_c)
        full_sc = gtk.CheckMenuItem("Full Screen")
        full_sc.connect("activate", self.full_screen)
        viewmenu.append(full_sc)
        source_mode = gtk.CheckMenuItem("Source Mode")
        source_mode.connect("activate", self.view_source_mode)
        viewmenu.append(source_mode)
        show_history = gtk.MenuItem("Show History")
        show_history.connect("activate", self.show_history)
        viewmenu.append(show_history)
        New_Window = gtk.MenuItem("New Window")
        New_Tab = gtk.MenuItem("New Tab")
        Open = gtk.MenuItem("Open")
        Save_As = gtk.MenuItem("Save As")
        filemenu.append(New_Window)
        filemenu.append(New_Tab)
        filemenu.append(Open)
        exi = gtk.MenuItem("Exit")

        New_Window.connect("activate", self.new_window_from_menu)
        New_Tab.connect("activate", self.new_tab_from_m)
        Open.connect("activate", self.open_file)
        Save_As.connect("activate", self.Save_as)
        exi.connect("activate", self.close)
       
        filemenu.append(Save_As)

        filemenu.append(exi)

        self.mb.append(filem)
        self.mb.append(view)
        self.mb.append(Options)
        self.mb.append(Tools)
        self.mb.append(Help)
        
        self.set_default_size(1000,700)
        self.connect('key-press-event',self.full_key)
        self.main_vbox = gtk.VBox(False, 1)
        self.add(self.main_vbox)
        self.main_vbox.pack_start(self.mb, False, True, 0)
        self.box2=gtk.HBox()
        self.addressbar=gtk.Entry()
        self.surf=gtk.ToolButton(gtk.STOCK_JUMP_TO)
        self.surf.set_tooltip(gtk.Tooltips(),('GO'))        
        self.forward=gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.forward.set_sensitive(False)
        self.back=gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.back.set_sensitive(False)        
        self.back.set_tooltip(gtk.Tooltips(),('GO_BACK'))        
        self.forward.set_tooltip(gtk.Tooltips(),('GO_FORWARD'))                
        self.stop_and_reload = gtk.ToolButton(gtk.STOCK_REFRESH)        
        self.box2.pack_start(self.back,False)
        self.box2.pack_start(self.forward,False)
        self.box2.pack_start(self.stop_and_reload,False)
        self.home_btn=gtk.ToolButton(gtk.STOCK_HOME)
        self.box2.pack_start(self.home_btn,False)         
        self.box2.pack_start(self.addressbar)
        self.stop_and_reload.set_tooltip(gtk.Tooltips(),('Stop and reload current page'))        
        self.stop_and_reload.connect('clicked', self.stop_and_reload_cb)
        self.home_btn.set_tooltip(gtk.Tooltips(),('Home Page'))
        self.home_btn.connect('clicked',self.go_home)
        self.box2.pack_start(self.surf,False)
        self.search_bar=gtk.Entry()
        self.search_bar.connect('activate',self.search)
        self.box2.pack_start(self.search_bar,False)
        self.search_btn=gtk.ToolButton(gtk.STOCK_FIND)
        self.search_btn.connect('clicked',self.search)
        self.box2.pack_start(self.search_btn,False)
        self.forward.connect('clicked',self.go_forward)
        self.back.connect('clicked', self.go_back)            
        self.page=BrowserPage()        
        self.addressbar.connect('activate',self.go)
        self.surf.connect('clicked',self.go)
        self.tabs=Console()
        self.tabs.connect('focus-view-title-changed',self.title_changed)        
        self.main_vbox.pack_start(self.box2, False, True, 0)
        self.main_vbox.pack_start(self.tabs, True, True, 0)
        self.statusbar = gtk.Statusbar()
        self.progressBar = gtk.ProgressBar()
        statusHBox = gtk.HBox(False, 0)
        self.iconbox = gtk.EventBox()
        self.iconbox.add(gtk.image_new_from_stock(gtk.STOCK_INFO, 16))
        self.statusbar.pack_start(self.iconbox, False, False, 6)
        self.statusbar.pack_start(self.progressBar, False,False, 7)
        statusHBox.pack_start(self.statusbar, True)
        self.main_vbox.pack_start(statusHBox, False)
        if url:
            thread=threading.Thread(target=(self.construct_tab(self.page,url)))
            thread.start()
        else:
            thread=threading.Thread(target=(self.construct_tab(self.page)))
            thread.start()
        self.show_all()
class ENGINE():
    def __init__(self):
        self.open_win=0
        self.db=db
        self.history_window=Hdb_window()

        
    def DB(self):
        con=sql.connect(self.db)
        try:
            con.execute('''CREATE TABLE IF NOT EXISTS urls(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             url LONGVARCHAR,
             title LONGVARCHAR,
             last_v_date TEXT,
             last_visit_time TEXT,
             visit_count INT);''')
    
            con.execute('''CREATE TABLE IF NOT EXISTS visits(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             url_id INTEGER,
             title LONGVARCHAR,
             site_url TEXT,
             v_date TEXT,
             visit_time TEXT );''')
            con.commit()
   
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()
    def h_window_info(self,w,num):
        info_win=Hdb_info(self.tree)
        info_win.connect('open',self.new_win_cb)
        info_win.show_info()
        info_win.show_all()
        
    def h_window(self,w,num):
        self.history_window.connect('open_info',self.h_window_info)
        self.history_window.connect('open',self.new_win_cb)

        self.tree,self.store=self.history_window.show_log()
        self.history_window.show_all()
    def update(self,w,uri,v_time,v_date):
        self.history_window.add_history(uri,v_time,v_date)

    def new_win_cb(self,w=None,uri=None):
        if uri:
            b=BROWSER(uri)
        else:
            b=BROWSER()
        b.connect('new-win',self.new_win_cb)
        b.connect('update-h',self.update)

        b.connect('download-file',self.download_file)
        b.connect('enable-caret',self.enable_caret)
        b.connect('enable-private',self.enable_private)
        b.connect('new-h',self.h_window)

        b.connect('destroy',self.destroy)
        b.start()
        self.open_win+=1
    def window(self):
        b=BROWSER()
        b.connect('update-h',self.update)

        b.connect('new-win',self.new_win_cb)
        b.connect('destroy',self.destroy)
        b.connect('download-file',self.download_file)
        b.connect('enable-caret',self.enable_caret)
        b.connect('enable-private',self.enable_private)
        b.connect('new-h',self.h_window)

        b.start()
        self.open_win+=1

    def enable_private(self,win,string):
        settings=win.page.get_settings()
        if string=='private_enabled':
            settings.set_property('enable-private-browsing',True)
            BROWSER.private_browsing=True
        else:
            settings.set_property('enable-private-browsing',False)
            BROWSER.private_browsing=False
        win.page.set_settings(settings) 

    def enable_caret(self,win,string):
        settings=win.page.get_settings()
        if string=='caret_enabled':
            settings.set_property('enable-caret-browsing',True)
        else:
            settings.set_property('enable-caret-browsing',False)            
        win.page.set_settings(settings) 

    def download_file(self,win,download):
        fc = gtk.FileChooserDialog(title="Save file as...", parent=None, buttons=(gtk.STOCK_SAVE, gtk.RESPONSE_OK,gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL), action=gtk.FILE_CHOOSER_ACTION_SAVE)
        fc.set_default_response(gtk.RESPONSE_OK)
        fname = download.get_suggested_filename()
        fc.set_current_name(fname) 
        res = fc.run()
        valid=False
        if  res == gtk.RESPONSE_OK:
            uri = fc.get_uri()            
        fc.destroy()
        path=download.get_uri()            
        thread=threading.Thread(target=(ret(path,uri,fname,fc) ))
        thread.start()

    def destroy(self,bro):
        self.open_win-=1
        if self.open_win==0:
            self.history_window.destroy()
            gtk.main_quit()
            #sys.Quit()
    def main(self):
        gtk.main()

    
def about_pywebkitgtk(menu_item, web_view):
    web_view.open("http://live.gnome.org/PyWebKitGtk")

def zoom_in_cb(menu_item, web_view):
    """Zoom into the page"""
    web_view.zoom_in()

def zoom_out_cb(menu_item, web_view):
    """Zoom out of the page"""
    web_view.zoom_out()
    
def zoom_hundred_cb(menu_item, web_view):
    """Zoom 100%"""
    if not (web_view.get_zoom_level() == 1.0):
        web_view.set_zoom_level(1.0)

def print_cb(menu_item, web_view):
    mainframe = web_view.get_main_frame()
    mainframe.print_full(gtk.PrintOperation(), gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG);

def hover_over_link(view, title, uri):
    BROWSER.url=uri
    BROWSER.tab_url=uri
    
def tab_label_style_set_cb (tab_label, style):
    context = tab_label.get_pango_context()
    metrics = context.get_metrics(tab_label.style.font_desc, context.get_language())
    char_width = metrics.get_approximate_digit_width()
    (width, height) = gtk.icon_size_lookup_for_settings(tab_label.get_settings(), gtk.ICON_SIZE_MENU)
    tab_label.set_size_request(20 * pango.PIXELS(char_width) + 2 * width, -1)
    button = tab_label.get_data("close-button")
    button.set_size_request(width + 4, height + 4)

    
engine=ENGINE()
engine.DB()
engine.window()
engine.main()
