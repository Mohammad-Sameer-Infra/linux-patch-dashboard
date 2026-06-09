def classify_updates(
    os_family,
    update_packages
):

    kernel_updates = 0
    security_updates = 0
    critical_packages = 0

    if os_family == "debian":

        kernel_updates = len([
            p for p in update_packages
            if "linux-image" in p
            or "linux-headers" in p
        ])

    elif os_family == "redhat":

        kernel_updates = len([
            p for p in update_packages
            if any(keyword in p.lower() for keyword in [
                "kernel",
                "kernel-core",
                "kernel-modules",
                "kernel-tools"
            ])
        ])

    security_updates = len([
        p for p in update_packages
        if any(keyword in p.lower() for keyword in [
            "openssl",
            "sudo",
            "systemd",
            "curl",
            "bash",
            "openssh"
        ])
    ])

    critical_packages = len([
        p for p in update_packages
        if any(keyword in p.lower() for keyword in [
            "kernel",
            "openssl",
            "systemd",
            "sudo"
        ])
    ])

    return {
        "kernel_updates": kernel_updates,
        "security_updates": security_updates,
        "critical_packages": critical_packages
    }
