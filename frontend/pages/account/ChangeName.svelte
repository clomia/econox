<script lang="ts">
    import Swal from "sweetalert2";

    const SwalStyle = {
        ...defaultSwalStyle,
        confirmButtonText: $Text.Submit,
        denyButtonText: $Text.Cancel,
    };

    Swal.fire({
        ...SwalStyle,
        input: "text",
        text: $Text.EnterNewName,
        preConfirm: async (newName: string) => {
            if (!newName) {
                Swal.showValidationMessage($Text.InsufficientInput);
                return;
            } else if (newName.length > 10) {
                Swal.showValidationMessage(format($Text.f_LengthLimit, { v: 10 }));
                return;
            }
            try {
                await api.private.patch("/user/name", { new_name: newName });
                location.reload();
            } catch {
                Swal.showValidationMessage($Text.UnexpectedError);
            }
        },
    });
</script>
