use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, RunEvent, WindowEvent,
};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;
use std::sync::{Mutex, atomic::{AtomicBool, Ordering}};

struct SidecarHolder(Mutex<Option<CommandChild>>);

struct AppState {
    minimize_to_tray: AtomicBool,
    is_quitting: AtomicBool,
}

#[tauri::command]
fn set_tray_setting(app: tauri::AppHandle, state: tauri::State<AppState>, min_to_tray: bool) {
    state.minimize_to_tray.store(min_to_tray, Ordering::Relaxed);

    // Dynamically add or remove the tray icon based on the setting
    if min_to_tray {
        if app.tray_by_id("main-tray").is_none() {
            if let Ok(quit_i) = MenuItem::with_id(&app, "quit", "Quit", true, None::<&str>) {
                if let Ok(show_i) = MenuItem::with_id(&app, "show", "Show App", true, None::<&str>) {
                    if let Ok(menu) = Menu::with_items(&app, &[&show_i, &quit_i]) {
                        if let Some(icon) = app.default_window_icon() {
                            let _ = TrayIconBuilder::with_id("main-tray")
                                .icon(icon.clone())
                                .menu(&menu)
                                .show_menu_on_left_click(false)
                                .tooltip("FitGirl Repacks Downloader")
                                .on_menu_event(|app, event| match event.id.as_ref() {
                                    "quit" => {
                                        let app_state = app.state::<AppState>();
                                        app_state.is_quitting.store(true, Ordering::Relaxed);
                                        let state = app.state::<SidecarHolder>();
                                        if let Some(child) = state.0.lock().unwrap().take() {
                                            let _ = child.kill();
                                        }
                                        #[cfg(target_os = "windows")]
                                        {
                                            use std::process::Command;
                                            let _ = Command::new("taskkill").args(["/F", "/IM", "server.exe", "/T"]).output();
                                        }
                                        app.exit(0);
                                    }
                                    "show" => {
                                        if let Some(window) = app.get_webview_window("main") {
                                            let _ = window.show();
                                            let _ = window.unminimize();
                                            let _ = window.set_focus();
                                        }
                                    }
                                    _ => {}
                                })
                                .on_tray_icon_event(|tray, event| {
                                    if let TrayIconEvent::Click {
                                        button: MouseButton::Left,
                                        button_state: MouseButtonState::Up,
                                        ..
                                    } = event {
                                        let app = tray.app_handle();
                                        if let Some(window) = app.get_webview_window("main") {
                                            let _ = window.show();
                                            let _ = window.unminimize();
                                            let _ = window.set_focus();
                                        }
                                    }
                                })
                                .build(&app);
                        }
                    }
                }
            }
        }
    } else {
        if let Some(tray) = app.remove_tray_by_id("main-tray") {
            drop(tray);
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarHolder(Mutex::new(None)))
        .manage(AppState { 
            minimize_to_tray: AtomicBool::new(false),
            is_quitting: AtomicBool::new(false),
        })
        .invoke_handler(tauri::generate_handler![set_tray_setting])
        .setup(|app| {
            let handle = app.handle().clone();
            
            // Spawn sidecar server
            match handle.shell().sidecar("server") {
                Ok(sidecar_command) => {
                    match sidecar_command.spawn() {
                        Ok((mut rx, child)) => {
                            let state = handle.state::<SidecarHolder>();
                            *state.0.lock().unwrap() = Some(child);

                            tauri::async_runtime::spawn(async move {
                                while let Some(event) = rx.recv().await {
                                    match event {
                                        CommandEvent::Stdout(line_bytes) => {
                                            println!("[sidecar stdout] {}", String::from_utf8_lossy(&line_bytes));
                                        }
                                        CommandEvent::Stderr(line_bytes) => {
                                            eprintln!("[sidecar stderr] {}", String::from_utf8_lossy(&line_bytes));
                                        }
                                        _ => {}
                                    }
                                }
                            });
                        }
                        Err(e) => eprintln!("Failed to spawn sidecar process: {}", e),
                    }
                }
                Err(e) => eprintln!("Failed to create sidecar command: {}", e),
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                let state = window.state::<AppState>();
                if state.minimize_to_tray.load(Ordering::Relaxed) {
                    let _ = window.hide();
                    api.prevent_close();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            let app_state = app_handle.state::<AppState>();
            app_state.is_quitting.store(true, Ordering::Relaxed);

            let state = app_handle.state::<SidecarHolder>();
            let child_opt = state.0.lock().unwrap().take();
            if let Some(child) = child_opt {
                let _ = child.kill();
            }

            #[cfg(target_os = "windows")]
            {
                use std::process::Command;
                let _ = Command::new("taskkill").args(["/F", "/IM", "server.exe", "/T"]).output();
            }
        }
    });
}